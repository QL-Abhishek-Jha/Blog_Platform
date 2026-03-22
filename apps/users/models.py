from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.conf import settings


class TimestampMixin(models.Model):
    "abstract mixin that adds created_at and updated_at to any model"
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class UserManager(BaseUserManager):

    def create_user(self, email, password=None, **extra_fields):
        "create a regular user — email is required and normalised before saving"
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        "create a superadmin user with all flags enabled — used by manage.py createsuperuser"
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_superadmin", True)
        extra_fields.setdefault("role", "admin")
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin, TimestampMixin):
    "custom user model: email login, three roles (user / author / admin)"

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
        "True if this user has the author role"
        return self.role == self.ROLE_AUTHOR

    @property
    def is_admin_user(self):
        "True if this user has the admin role"
        return self.role == self.ROLE_ADMIN

    def _is_protected(self):
        "returns True for staff or superadmin accounts — admins cannot modify these"
        return self.is_staff or self.is_superadmin


class SubscriptionManager(models.Manager):

    def subscribers_of(self, author):
        "return all Subscription rows where author= the given user"
        return self.filter(author=author).select_related("subscriber")

    def is_subscribed(self, subscriber, author):
        "True if subscriber already follows this author"
        return self.filter(subscriber=subscriber, author=author).exists()


class Subscription(TimestampMixin):
    "a user follows an author — unique_together prevents duplicate subscriptions"

    subscriber = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="subscriptions",
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="followers",
    )

    objects = SubscriptionManager()

    class Meta:
        db_table = "subscriptions"
        unique_together = ("subscriber", "author")
        ordering = ["-created_at"]

    def clean(self):
        "prevent a user from subscribing to themselves at the model level"
        from django.core.exceptions import ValidationError
        if self.subscriber == self.author:
            raise ValidationError("You cannot subscribe to yourself.")

    def save(self, *args, **kwargs):
        "run full_clean before saving so clean() is always enforced"
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.subscriber.username} → {self.author.username}"