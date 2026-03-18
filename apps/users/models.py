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
    # roles: user (default), author (promoted by admin), admin (created via Django panel)

    ROLE_USER   = "user"
    ROLE_AUTHOR = "author"
    ROLE_ADMIN  = "admin"

    ROLE_CHOICES = (
        (ROLE_USER,   "User"),
        (ROLE_AUTHOR, "Author"),
        (ROLE_ADMIN,  "Admin"),
    )

    username    = models.CharField(max_length=150, unique=True)
    email       = models.EmailField(unique=True)
    first_name  = models.CharField(max_length=100, blank=True)
    last_name   = models.CharField(max_length=100, blank=True)
    role        = models.CharField(max_length=10, choices=ROLE_CHOICES, default=ROLE_USER)
    bio         = models.TextField(blank=True)
    profile_pic = models.ImageField(upload_to="profile_pics/", null=True, blank=True)
    is_active   = models.BooleanField(default=True)
    is_staff    = models.BooleanField(default=False)
    is_superadmin = models.BooleanField(default=False)

    USERNAME_FIELD  = "email"
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

    def _is_protected(self):
        # prevents admin from modifying staff or superadmin accounts
        return self.is_staff or self.is_superadmin


class SubscriptionManager(models.Manager):

    def subscribers_of(self, author):
        return self.filter(author=author).select_related("subscriber")

    def is_subscribed(self, subscriber, author):
        return self.filter(subscriber=subscriber, author=author).exists()


class Subscription(TimestampMixin):
    # a user subscribes to an author — unique_together prevents duplicate subscriptions
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
        from django.core.exceptions import ValidationError
        if self.subscriber == self.author:
            raise ValidationError("You cannot subscribe to yourself.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.subscriber.username} → {self.author.username}"