import uuid
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.conf import settings



class TimestampMixin(models.Model):
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True



class UserManager(BaseUserManager):

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_superadmin", True)
        extra_fields.setdefault("role", "admin")
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin, TimestampMixin):
    """
    Custom user model.
    Roles:
      - user   (default, registered via API)
      - author (promoted by admin)
      - admin  (created by superadmin from Django panel or superadmin API)
    Superuser has full Django admin access.
    """

    ROLE_USER = "user"
    ROLE_AUTHOR = "author"
    ROLE_ADMIN = "admin"

    ROLE_CHOICES = (
        (ROLE_USER, "User"),
        (ROLE_AUTHOR, "Author"),
        (ROLE_ADMIN, "Admin"),
    )

    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default=ROLE_USER)
    bio = models.TextField(blank=True)
    profile_pic = models.ImageField(upload_to="profile_pics/", null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superadmin = models.BooleanField(default=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    objects = UserManager()

    class Meta:
        db_table = "users"
        ordering = ["-created_at"]

    def __str__(self):
        return self.email

    @property
    def is_author(self):
        return self.role == self.ROLE_AUTHOR

    @property
    def is_admin_user(self):
        return self.role == self.ROLE_ADMIN

class PasswordResetToken(TimestampMixin):
    "Stores password reset tokens. Link-based reset — no email service needed."
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reset_tokens")
    token = models.UUIDField(default=uuid.uuid4, unique=True)
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)

    class Meta:
        db_table = "password_reset_tokens"

    def __str__(self):
        return f"Reset token for {self.user.email}"


class SubscriptionManager(models.Manager):
    "Custom manager for Subscription model."

    def subscribers_of(self, author):
        """Return all subscriptions for a given author."""
        return self.filter(author=author).select_related("subscriber")

    def is_subscribed(self, subscriber, author):
        """Check if a user is subscribed to an author."""
        return self.filter(subscriber=subscriber, author=author).exists()


class Subscription(TimestampMixin):
    """
    Subscription table — a user subscribes to an author.
    Constraints:
      - A user can subscribe to an author only once (unique_together).
      - A subscriber cannot subscribe to themselves (enforced in clean()).
    """
    subscriber = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="subscriptions",
        help_text="The user who is subscribing",
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="followers",
        help_text="The author being subscribed to",
    )

    objects = SubscriptionManager()

    class Meta:
        db_table = "subscriptions"
        unique_together = ("subscriber", "author")
        ordering = ["-created_at"]

    def clean(self):
        "Subscriber cannot subscribe to themselves."
        from django.core.exceptions import ValidationError
        if self.subscriber == self.author:
            raise ValidationError("You cannot subscribe to yourself.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.subscriber.username} → {self.author.username}"