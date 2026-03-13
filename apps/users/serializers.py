from rest_framework import serializers
from django.contrib.auth import authenticate
from django.utils.encoding import force_bytes, smart_str, DjangoUnicodeDecodeError
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from rest_framework.exceptions import ValidationError

from .models import User, Subscription


class UserRegistrationSerializer(serializers.ModelSerializer):
    "Handles user registration with password confirmation."
    confirm_password = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ["id", "username", "email", "password", "confirm_password", "first_name", "last_name"]

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already registered")
        return value

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username already taken")
        return value

    def validate(self, data):
        if data["password"] != data["confirm_password"]:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match"})
        return data

    def create(self, validated_data):
        validated_data.pop("confirm_password")
        return User.objects.create_user(**validated_data)


class UserLoginSerializer(serializers.Serializer):
    "Validates login credentials and returns authenticated user."
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        email = data.get("email")
        password = data.get("password")

        if not email or not password:
            raise serializers.ValidationError("Email and password are required")

        user = authenticate(email=email, password=password)
        if not user:
            raise serializers.ValidationError("Invalid email or password")

        if not user.is_active:
            raise serializers.ValidationError("Account is disabled")

        data["user"] = user
        return data


class ChangePasswordSerializer(serializers.Serializer):
    "Validates old password and ensures new passwords match."
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)
    confirm_new_password = serializers.CharField(write_only=True)

    def validate(self, data):
        if data["new_password"] != data["confirm_new_password"]:
            raise serializers.ValidationError(
                {"confirm_new_password": "New passwords do not match"}
            )
        return data


class ForgotPasswordSerializer(serializers.Serializer):
    
    "Generates a password reset link and prints it in terminal."
    email = serializers.EmailField()

    def validate(self, attrs):
        email = attrs.get("email")
        # Silently skip if email not found — do not expose registration status
        if User.objects.filter(email=email).exists():
            user = User.objects.get(email=email)
            uid = urlsafe_base64_encode(force_bytes(user.id))
            token = PasswordResetTokenGenerator().make_token(user)
            link = f"http://localhost:8000/api/auth/reset-password/{uid}/{token}/"
            print("Password Reset Link:", link)
        return attrs


class ResetPasswordSerializer(serializers.Serializer):
    "Validates reset token and sets new password."
    password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        try:
            password = attrs.get("password")
            confirm_password = attrs.get("confirm_password")
            uid = self.context.get("uid")
            token = self.context.get("token")

            if password != confirm_password:
                raise serializers.ValidationError({"confirm_password": "Passwords do not match"})

            user_id = smart_str(urlsafe_base64_decode(uid))
            user = User.objects.get(id=user_id)

            if not PasswordResetTokenGenerator().check_token(user, token):
                raise ValidationError("Token is not valid or expired")

            user.set_password(password)
            user.save()
            return attrs

        except DjangoUnicodeDecodeError:
            raise ValidationError("Token is not valid or expired")


class UserProfileSerializer(serializers.ModelSerializer):
    "Full profile — for authenticated user viewing/editing their own profile."

    class Meta:
        model = User
        fields = [
            "id", "username", "email", "first_name", "last_name",
            "role", "bio", "profile_pic", "is_active", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "email", "role", "is_active", "created_at", "updated_at"]


class PublicUserProfileSerializer(serializers.ModelSerializer):
    """Public author profile — hides sensitive fields."""

    class Meta:
        model = User
        fields = ["id", "username", "first_name", "last_name", "bio", "profile_pic"]



class AdminUserUpdateSerializer(serializers.ModelSerializer):
    """
    Admin can update: role (user/author only) and is_active.
    Admin CANNOT set role to 'admin' — only superadmin can from Django panel.
    """

    class Meta:
        model = User
        fields = ["role", "is_active"]

    def validate_role(self, value):
        if value not in ("user", "author"):
            raise serializers.ValidationError("You can only set role to 'user' or 'author'.")
        return value
    
class SubscriptionSerializer(serializers.ModelSerializer):
    """Shows subscription details."""
    author_username = serializers.CharField(source="author.username", read_only=True)
    subscriber_username = serializers.CharField(source="subscriber.username", read_only=True)

    class Meta:
        model = Subscription
        fields = ["id", "subscriber", "subscriber_username", "author", "author_username", "created_at"]
        read_only_fields = ["id", "subscriber", "subscriber_username", "author_username", "created_at"]