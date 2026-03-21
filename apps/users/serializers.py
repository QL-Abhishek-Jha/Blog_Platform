from rest_framework import serializers
from django.contrib.auth import authenticate
from django.utils.encoding import force_bytes, smart_str, DjangoUnicodeDecodeError
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.auth.tokens import PasswordResetTokenGenerator

from .models import User, Subscription


class UserRegistrationSerializer(serializers.ModelSerializer):
    confirm_password = serializers.CharField(write_only=True)
    password         = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model            = User
        fields           = ["id", "username", "email", "password", "confirm_password", "first_name", "last_name"]
        read_only_fields = ["id"]

    def validate(self, data):
        errors = {}

        email    = data.get("email", "").lower()
        username = data.get("username", "")
        password = data.get("password", "")
        confirm  = data.get("confirm_password", "")

        if User.objects.filter(email=email).exists():
            errors["email"] = "Email already registered."

        if User.objects.filter(username=username).exists():
            errors["username"] = "Username already taken."

        if password != confirm:
            errors["confirm_password"] = "Passwords do not match."

        if errors:
            raise serializers.ValidationError(errors)

        data["email"] = email
        return data

    def create(self, validated_data):
        validated_data.pop("confirm_password")
        return User.objects.create_user(**validated_data)


class UserLoginSerializer(serializers.Serializer):
    email    = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        email    = data.get("email", "")
        password = data.get("password", "")

        user = authenticate(email=email, password=password)

        if not user:
            raise serializers.ValidationError({"non_field_errors": "Invalid email or password."})
        if not user.is_active:
            raise serializers.ValidationError({"non_field_errors": "Account is disabled."})

        data["user"] = user
        return data


class ChangePasswordSerializer(serializers.Serializer):
    old_password         = serializers.CharField(write_only=True)
    new_password         = serializers.CharField(write_only=True, min_length=8)
    confirm_new_password = serializers.CharField(write_only=True)

    def validate(self, data):
        errors = {}

        old_password = data.get("old_password", "")
        new_password = data.get("new_password", "")
        confirm      = data.get("confirm_new_password", "")

        if new_password != confirm:
            errors["confirm_new_password"] = "Passwords do not match."

        if old_password == new_password:
            errors["new_password"] = "New password cannot be the same as old password."

        if errors:
            raise serializers.ValidationError(errors)

        return data


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate(self, attrs):
        email = attrs.get("email", "").lower()

        user = User.objects.filter(email=email).first()
        if user:
            uid   = urlsafe_base64_encode(force_bytes(user.id))
            token = PasswordResetTokenGenerator().make_token(user)
            link  = f"http://localhost:8000/api/auth/reset-password/{uid}/{token}/"
            # TODO: send link via email service
            # print("Password Reset Link:", link)

        attrs["email"] = email
        return attrs


class ResetPasswordSerializer(serializers.Serializer):
    password         = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        errors = {}

        password         = attrs.get("password", "")
        confirm_password = attrs.get("confirm_password", "")
        uid              = self.context.get("uid")
        token            = self.context.get("token")

        if password != confirm_password:
            errors["confirm_password"] = "Passwords do not match."

        if errors:
            raise serializers.ValidationError(errors)

        try:
            user_id = smart_str(urlsafe_base64_decode(uid))
            user    = User.objects.get(id=user_id)

            if not PasswordResetTokenGenerator().check_token(user, token):
                raise serializers.ValidationError({"token": "Reset link is invalid or has expired."})

            attrs["user"] = user
            return attrs

        except (User.DoesNotExist, DjangoUnicodeDecodeError, ValueError, TypeError):
            raise serializers.ValidationError({"token": "Reset link is invalid or has expired."})


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model            = User
        fields           = ["id", "username", "email", "first_name", "last_name", "role", "bio", "profile_pic", "created_at"]
        read_only_fields = ["id", "email", "role", "created_at"]


class PublicAuthorProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model  = User
        fields = ["username", "first_name", "last_name", "bio", "profile_pic"]


class AdminUserSerializer(serializers.ModelSerializer):
    class Meta:
        model            = User
        fields           = ["id", "username", "email", "role", "is_active", "created_at"]
        read_only_fields = ["id", "username", "email", "role", "is_active", "created_at"]


class AdminUserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model  = User
        fields = ["role", "is_active"]

    def validate(self, data):
        role = data.get("role")

        if role is not None and role not in ("user", "author"):
            raise serializers.ValidationError({"role": "Role must be 'user' or 'author'."})

        return data


class SubscriptionSerializer(serializers.ModelSerializer):
    author_username = serializers.CharField(source="author.username", read_only=True, default=None)
    author_bio      = serializers.CharField(source="author.bio",      read_only=True, default="")

    class Meta:
        model            = Subscription
        fields           = ["id", "author_username", "author_bio", "created_at"]
        read_only_fields = ["id", "author_username", "author_bio", "created_at"]