import logging

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
from core.permissions import IsAdminUser

User   = get_user_model()
logger = logging.getLogger("apps")


def _blacklist_all_user_tokens(user):
    tokens = OutstandingToken.objects.filter(user=user)
    for token in tokens:
        BlacklistedToken.objects.get_or_create(token=token)


class UserRegistrationView(APIView):
    authentication_classes = []
    permission_classes     = [AllowAny]

    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        user = serializer.save()
        logger.info(f"New user registered: {user.email}")
        return Response(
            {"message": "Registration successful", "user_id": user.id},
            status=status.HTTP_201_CREATED,
        )


class UserLoginView(APIView):
    authentication_classes = []
    permission_classes     = [AllowAny]

    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        if not serializer.is_valid():
            email = request.data.get("email", "unknown")
            logger.warning(f"Failed login attempt for email: {email}")
            return Response(serializer.errors, status=status.HTTP_401_UNAUTHORIZED)
        user    = serializer.validated_data["user"]
        refresh = RefreshToken.for_user(user)
        logger.info(f"User logged in: {user.email} | role: {user.role}")
        return Response(
            {
                "access_token":  str(refresh.access_token),
                "refresh_token": str(refresh),
                "user": {"id": user.id, "email": user.email, "role": user.role},
            },
            status=status.HTTP_200_OK,
        )


class TokenRefreshView(APIView):
    authentication_classes = []
    permission_classes     = [AllowAny]

    def post(self, request):
        refresh_token = request.data.get("refresh_token")
        if not refresh_token:
            return Response({"error": "refresh_token is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            old_refresh = RefreshToken(refresh_token)
            user_id     = old_refresh.payload.get("user_id")
            user        = User.objects.filter(id=user_id).first()
            if not user:
                return Response({"error": "User not found. Please login again."}, status=status.HTTP_401_UNAUTHORIZED)
            old_refresh.blacklist()
            new_refresh = RefreshToken.for_user(user)
            logger.info(f"Token refreshed for user: {user.email}")
            return Response(
                {
                    "access_token":  str(new_refresh.access_token),
                    "refresh_token": str(new_refresh),
                    "user": {"id": user.id, "email": user.email, "role": user.role},
                },
                status=status.HTTP_200_OK,
            )
        except TokenError:
            logger.warning("Expired token refresh attempt")
            return Response(
                {"error": "Refresh token is expired. Please login again.", "code": "token_expired"},
                status=status.HTTP_401_UNAUTHORIZED,
            )


class UserLogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get("refresh_token")
        if not refresh_token:
            return Response({"error": "refresh_token is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            logger.info(f"User logged out: {request.user.email}")
        except TokenError:
            return Response({"error": "Token is invalid or expired"}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"message": "Logged out successfully"}, status=status.HTTP_200_OK)


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        user = request.user
        if not user.check_password(serializer.validated_data["old_password"]):
            logger.warning(f"Wrong old password attempt by: {user.email}")
            return Response({"error": "Old password is incorrect"}, status=status.HTTP_400_BAD_REQUEST)
        user.set_password(serializer.validated_data["new_password"])
        user.save()
        _blacklist_all_user_tokens(user)
        logger.info(f"Password changed for user: {user.email} — all sessions blacklisted")
        return Response({"message": "Password changed successfully"}, status=status.HTTP_200_OK)


class ForgotPasswordView(APIView):
    authentication_classes = []
    permission_classes     = [AllowAny]

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        email = request.data.get("email", "unknown")
        logger.info(f"Password reset requested for email: {email}")
        return Response(
            {"message": "If this email is registered, a password reset link has been sent."},
            status=status.HTTP_200_OK,
        )


class ResetPasswordView(APIView):
    authentication_classes = []
    permission_classes     = [AllowAny]

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
        logger.info(f"Password reset successfully for user: {user.email}")
        return Response({"message": "Password reset successfully. Please login."}, status=status.HTTP_200_OK)


class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request):
        # BUG FIX: was UserProfileSerializer(request.data, partial=True) — missing instance
        serializer = UserProfileSerializer(request.user, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        logger.info(f"Profile updated for user: {request.user.email}")
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request):
        password = request.data.get("password")
        if not password:
            return Response({"error": "Password is required to delete your account."}, status=status.HTTP_400_BAD_REQUEST)
        if not request.user.check_password(password):
            return Response({"error": "Incorrect password."}, status=status.HTTP_400_BAD_REQUEST)
        email = request.user.email
        request.user.delete()
        logger.info(f"Account permanently deleted: {email}")
        return Response({"message": "Your account has been permanently deleted."}, status=status.HTTP_200_OK)


class PublicAuthorProfileView(APIView):
    authentication_classes = []
    permission_classes     = [AllowAny]

    def get(self, request, username):
        user = User.objects.filter(username=username, role=User.ROLE_AUTHOR, is_active=True).first()
        if not user:
            return Response({"error": "Author not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = PublicAuthorProfileSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)


class SubscribeAuthorView(APIView):
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
        logger.info(f"User {request.user.email} subscribed to author {author.email}")
        return Response({"message": f"Subscribed to {author.username}"}, status=status.HTTP_201_CREATED)


class UnsubscribeAuthorView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, username):
        author = User.objects.filter(username=username, role=User.ROLE_AUTHOR, is_active=True).first()
        if not author:
            return Response({"error": "Author not found"}, status=status.HTTP_404_NOT_FOUND)
        subscription = Subscription.objects.filter(subscriber=request.user, author=author).first()
        if not subscription:
            return Response({"error": "Not subscribed"}, status=status.HTTP_400_BAD_REQUEST)
        subscription.delete()
        logger.info(f"User {request.user.email} unsubscribed from author {author.email}")
        return Response({"message": f"Unsubscribed from {author.username}"}, status=status.HTTP_200_OK)


class MySubscriptionsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        subscriptions = Subscription.objects.filter(subscriber=request.user).select_related("author")
        serializer    = SubscriptionSerializer(subscriptions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class AdminUserListView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        users      = User.objects.all()
        serializer = AdminUserSerializer(users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class AdminUserDetailView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def _get_user(self, user_id):
        return User.objects.filter(id=user_id).first()

    def _check_protected(self, user):
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
        user.refresh_from_db()
        logger.info(f"Admin {request.user.email} updated user {user.email} — role: {user.role} | active: {user.is_active}")
        return Response(AdminUserSerializer(user).data, status=status.HTTP_200_OK)

    def delete(self, request, user_id):
        user = self._get_user(user_id)
        if not user:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        guard = self._check_protected(user)
        if guard:
            return guard
        email = user.email
        user.delete()
        logger.info(f"Admin {request.user.email} deleted user {email}")
        return Response(status=status.HTTP_204_NO_CONTENT)