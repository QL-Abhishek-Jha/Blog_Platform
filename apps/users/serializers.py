from rest_framework import serializers
from django.contrib.auth import authenticate
from django.utils.encoding import force_bytes, smart_str, DjangoUnicodeDecodeError
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from rest_framework.exceptions import ValidationError

from .models import User, Subscription


class UserRegistrationSerializer(serializers.ModelSerializer):
    # confirm_password is write only, not saved to db
    confirm_password = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ["id", "username", "email", "password", "confirm_password", "first_name", "last_name"]
        read_only_fields = ["id"]

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already registered.")
        return value.lower()

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username already taken.")
        return value

    def validate(self, data):
        if data["password"] != data["confirm_password"]:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})
        return data

    def create(self, validated_data):
        validated_data.pop("confirm_password")
        return User.objects.create_user(**validated_data)


class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = authenticate(email=data.get("email"), password=data.get("password"))
        if not user:
            raise serializers.ValidationError("Invalid email or password.")
        if not user.is_active:
            raise serializers.ValidationError("Account is disabled.")
        data["user"] = user
        return data


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)
    confirm_new_password = serializers.CharField(write_only=True)

    def validate(self, data):
        if data["new_password"] != data["confirm_new_password"]:
            raise serializers.ValidationError({"confirm_new_password": "Passwords do not match."})
        if data["old_password"] == data["new_password"]:
            raise serializers.ValidationError({"new_password": "New password cannot be the same as old password."})
        return data


class ForgotPasswordSerializer(serializers.Serializer):
    # silently skips unknown emails to avoid exposing registered accounts
    email = serializers.EmailField()

    def validate(self, attrs):
        email = attrs.get("email")
        if User.objects.filter(email=email).exists():
            user = User.objects.get(email=email)
            uid = urlsafe_base64_encode(force_bytes(user.id))
            token = PasswordResetTokenGenerator().make_token(user)
            link = f"http://localhost:8000/api/auth/reset-password/{uid}/{token}/"
            print("Password Reset Link:", link)
        return attrs


class ResetPasswordSerializer(serializers.Serializer):
    # validates token and returns user — actual password save is done in the view
    password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        try:
            password = attrs.get("password")
            confirm_password = attrs.get("confirm_password")
            uid = self.context.get("uid")
            token = self.context.get("token")

            if password != confirm_password:
                raise serializers.ValidationError({"confirm_password": "Passwords do not match."})

            user_id = smart_str(urlsafe_base64_decode(uid))
            user = User.objects.get(id=user_id)

            if not PasswordResetTokenGenerator().check_token(user, token):
                raise ValidationError("Reset link is invalid or has expired.")

            attrs["user"] = user
            return attrs

        except DjangoUnicodeDecodeError:
            raise ValidationError("Reset link is invalid or has expired.")


class UserProfileSerializer(serializers.ModelSerializer):
    # authenticated user viewing or updating their own profile
    class Meta:
        model = User
        fields = [
            "id", "username", "email", "first_name", "last_name",
            "role", "bio", "profile_pic", "created_at",
        ]
        read_only_fields = ["id", "email", "role", "created_at"]


class PublicAuthorProfileSerializer(serializers.ModelSerializer):
    # public facing, only what a visitor needs to see
    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "bio", "profile_pic"]


class AdminUserSerializer(serializers.ModelSerializer):
    # admin viewing a user — includes role and active status
    class Meta:
        model = User
        fields = ["id", "username", "email", "role", "is_active", "created_at"]
        read_only_fields = fields


class AdminUserUpdateSerializer(serializers.ModelSerializer):
    # admin can only toggle role (user/author) and active status
    class Meta:
        model = User
        fields = ["role", "is_active"]

    def validate_role(self, value):
        if value not in ("user", "author"):
            raise serializers.ValidationError("Role must be 'user' or 'author'.")
        return value


class SubscriptionSerializer(serializers.ModelSerializer):
    # shows author info instead of raw ids
    author_username = serializers.CharField(source="author.username", read_only=True)
    author_bio = serializers.CharField(source="author.bio", read_only=True)

    class Meta:
        model = Subscription
        fields = ["id", "author_username", "author_bio", "created_at"]
        read_only_fields = fields