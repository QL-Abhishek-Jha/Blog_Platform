from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken

from .models import Subscription
from .serializers import (
    UserRegistrationSerializer,
    UserLoginSerializer,
    UserProfileSerializer,
    ChangePasswordSerializer,
    ForgotPasswordSerializer,
    ResetPasswordSerializer,
    PublicAuthorProfileSerializer,
    SubscriptionSerializer,
    AdminUserSerializer,
    AdminUserUpdateSerializer,
)
from .permissions import IsAdminUser

User = get_user_model()


def _blacklist_all_user_tokens(user):
    # invalidates all refresh tokens on password change
    tokens = OutstandingToken.objects.filter(user=user)
    for token in tokens:
        BlacklistedToken.objects.get_or_create(token=token)


class UserRegistrationView(APIView):
    # public — anyone can register

    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        user = serializer.save()
        return Response(
            {"message": "Registration successful", "user_id": user.id},
            status=status.HTTP_201_CREATED,
        )


class UserLoginView(APIView):
    # public — returns access and refresh tokens on success

    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_401_UNAUTHORIZED)
        user = serializer.validated_data["user"]
        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "access_token": str(refresh.access_token),
                "refresh_token": str(refresh),
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "role": user.role,
                },
            },
            status=status.HTTP_200_OK,
        )


class TokenRefreshView(APIView):
    # public — rotates refresh token and returns new pair

    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        refresh_token = request.data.get("refresh_token")
        if not refresh_token:
            return Response({"error": "refresh_token is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            old_refresh = RefreshToken(refresh_token)
            user_id = old_refresh.payload.get("user_id")
            user = User.objects.filter(id=user_id).first()
            if not user:
                return Response({"error": "User not found. Please login again."}, status=status.HTTP_401_UNAUTHORIZED)
            old_refresh.blacklist()
            new_refresh = RefreshToken.for_user(user)
            return Response(
                {
                    "access_token": str(new_refresh.access_token),
                    "refresh_token": str(new_refresh),
                    "user": {
                        "id": user.id,
                        "email": user.email,
                        "role": user.role,
                    },
                },
                status=status.HTTP_200_OK,
            )
        except TokenError:
            return Response(
                {"error": "Refresh token is expired. Please login again.", "code": "token_expired"},
                status=status.HTTP_401_UNAUTHORIZED,
            )


class UserLogoutView(APIView):
    # blacklists the provided refresh token

    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get("refresh_token")
        if not refresh_token:
            return Response({"error": "refresh_token is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except TokenError:
            return Response({"error": "Token is invalid or expired"}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"message": "Logged out successfully"}, status=status.HTTP_200_OK)


class ChangePasswordView(APIView):
    # blacklists all sessions after password change

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        user = request.user
        if not user.check_password(serializer.validated_data["old_password"]):
            return Response({"error": "Old password is incorrect"}, status=status.HTTP_400_BAD_REQUEST)
        user.set_password(serializer.validated_data["new_password"])
        user.save()
        _blacklist_all_user_tokens(user)
        return Response({"message": "Password changed successfully"}, status=status.HTTP_200_OK)


class ForgotPasswordView(APIView):
    # public — prints reset link in terminal, silently skips unknown emails

    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response(
            {"message": "If this email is registered, a password reset link has been sent. Check your terminal."},
            status=status.HTTP_200_OK,
        )


class ResetPasswordView(APIView):
    # public — validates token then saves new password

    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request, uid, token):
        serializer = ResetPasswordSerializer(
            data=request.data,
            context={"uid": uid, "token": token},
        )
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        user = serializer.validated_data["user"]
        user.set_password(serializer.validated_data["password"])
        user.save()
        return Response({"message": "Password reset successfully. Please login."}, status=status.HTTP_200_OK)


class UserProfileView(APIView):
    # logged in user can view, update, or delete their own account

    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request):
        serializer = UserProfileSerializer(request.user, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request):
        # requires password confirmation before permanent deletion
        password = request.data.get("password")
        if not password:
            return Response({"error": "Password is required to delete your account."}, status=status.HTTP_400_BAD_REQUEST)
        if not request.user.check_password(password):
            return Response({"error": "Incorrect password."}, status=status.HTTP_400_BAD_REQUEST)
        request.user.delete()
        return Response({"message": "Your account has been permanently deleted."}, status=status.HTTP_200_OK)


class PublicAuthorProfileView(APIView):
    # public — returns author's public profile

    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request, username):
        user = User.objects.filter(username=username, role=User.ROLE_AUTHOR, is_active=True).first()
        if not user:
            return Response({"error": "Author not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = PublicAuthorProfileSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)


class SubscribeAuthorView(APIView):
    # logged in user subscribes to an author

    permission_classes = [IsAuthenticated]

    def post(self, request, username):
        author = User.objects.filter(username=username, role=User.ROLE_AUTHOR, is_active=True).first()
        if not author:
            return Response({"error": "Author not found"}, status=status.HTTP_404_NOT_FOUND)
        if request.user == author:
            return Response({"error": "You cannot subscribe to yourself"}, status=status.HTTP_400_BAD_REQUEST)
        if Subscription.objects.is_subscribed(subscriber=request.user, author=author):
            return Response({"error": "Already subscribed"}, status=status.HTTP_400_BAD_REQUEST)
        Subscription.objects.create(subscriber=request.user, author=author)
        return Response({"message": f"Subscribed to {author.username}"}, status=status.HTTP_201_CREATED)


class UnsubscribeAuthorView(APIView):
    # logged in user unsubscribes from an author

    permission_classes = [IsAuthenticated]

    def delete(self, request, username):
        author = User.objects.filter(username=username, role=User.ROLE_AUTHOR, is_active=True).first()
        if not author:
            return Response({"error": "Author not found"}, status=status.HTTP_404_NOT_FOUND)
        subscription = Subscription.objects.filter(subscriber=request.user, author=author).first()
        if not subscription:
            return Response({"error": "Not subscribed"}, status=status.HTTP_400_BAD_REQUEST)
        subscription.delete()
        return Response({"message": f"Unsubscribed from {author.username}"}, status=status.HTTP_200_OK)


class MySubscriptionsView(APIView):
    # logged in user sees authors they follow

    permission_classes = [IsAuthenticated]

    def get(self, request):
        subscriptions = Subscription.objects.filter(subscriber=request.user).select_related("author")
        serializer = SubscriptionSerializer(subscriptions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class AdminUserListView(APIView):
    # admin only — list all users

    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        users = User.objects.all()
        serializer = AdminUserSerializer(users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class AdminUserDetailView(APIView):
    # admin only — view, update role/status, or delete a user

    permission_classes = [IsAuthenticated, IsAdminUser]

    def _get_user(self, user_id):
        return User.objects.filter(id=user_id).first()

    def _check_protected(self, user):
        # prevents admin from modifying other admins or superadmins
        if user._is_protected():
            return Response(
                {"error": "Cannot modify admin or superadmin accounts"},
                status=status.HTTP_403_FORBIDDEN,
            )
        return None

    def get(self, request, user_id):
        user = self._get_user(user_id)
        if not user:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = AdminUserSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, user_id):
        user = self._get_user(user_id)
        if not user:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        guard = self._check_protected(user)
        if guard:
            return guard
        serializer = AdminUserUpdateSerializer(user, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response(AdminUserSerializer(user).data, status=status.HTTP_200_OK)

    def delete(self, request, user_id):
        user = self._get_user(user_id)
        if not user:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        guard = self._check_protected(user)
        if guard:
            return guard
        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)