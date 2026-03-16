from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken, OutstandingToken, BlacklistedToken
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
    PublicUserProfileSerializer,
    SubscriptionSerializer,
    AdminUserUpdateSerializer,
)
from .permissions import IsAdminUser, IsSuperAdmin

User = get_user_model()


# ── Shared helpers ────────────────────────────────────────────────────────────

def _get_object_or_404(queryset_or_model, **kwargs):
    """
    Returns the first object matching kwargs, or a 404 Response.
    Usage:
        result = _get_object_or_404(User, id=user_id)
        if isinstance(result, Response):
            return result
    """
    if hasattr(queryset_or_model, 'filter'):
        obj = queryset_or_model.filter(**kwargs).first()
    else:
        obj = queryset_or_model.objects.filter(**kwargs).first()
    if obj is None:
        model_name = getattr(queryset_or_model, '__name__', 'Object')
        return Response({"error": f"{model_name} not found"}, status=status.HTTP_404_NOT_FOUND)
    return obj


def _blacklist_all_user_tokens(user):
    """Blacklist all outstanding refresh tokens for a user (used on password change)."""
    tokens = OutstandingToken.objects.filter(user=user)
    for token in tokens:
        BlacklistedToken.objects.get_or_create(token=token)


# ── Auth views ────────────────────────────────────────────────────────────────

class UserRegistrationView(APIView):
    """
    POST /api/auth/register/
    Registers a new user. Anyone can access it.
    Request body: username, email, password, confirm_password, first_name, last_name
    """

    authentication_classes = []
    permission_classes     = [AllowAny]

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
    """
    POST /api/auth/login/
    Request body: email, password
    Response: access_token, refresh_token
    """

    authentication_classes = []
    permission_classes     = [AllowAny]

    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_401_UNAUTHORIZED)

        user    = serializer.validated_data["user"]
        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "access_token":  str(refresh.access_token),
                "refresh_token": str(refresh),
                "user": {
                    "id":    user.id,
                    "email": user.email,
                    "role":  user.role,
                },
            },
            status=status.HTTP_200_OK,
        )


class TokenRefreshView(APIView):
    """
    POST /api/auth/token/refresh/
    Request body: refresh_token
    """

    authentication_classes = []
    permission_classes     = [AllowAny]

    def post(self, request):
        refresh_token = request.data.get("refresh_token")
        if not refresh_token:
            return Response(
                {"error": "refresh_token is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            old_refresh = RefreshToken(refresh_token)
            user_id     = old_refresh.payload.get("user_id")
            user        = User.objects.filter(id=user_id).first()

            if not user:
                return Response(
                    {"error": "User not found. Please login again."},
                    status=status.HTTP_401_UNAUTHORIZED,
                )

            old_refresh.blacklist()
            new_refresh = RefreshToken.for_user(user)

            return Response(
                {
                    "access_token":  str(new_refresh.access_token),
                    "refresh_token": str(new_refresh),
                    "user": {
                        "id":    user.id,
                        "email": user.email,
                        "role":  user.role,
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
    """
    POST /api/auth/logout/
    Request body: refresh_token
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get("refresh_token")
        if not refresh_token:
            return Response(
                {"error": "refresh_token is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except TokenError:
            return Response(
                {"error": "Token is invalid or expired"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response({"message": "Logged out successfully"}, status=status.HTTP_200_OK)


class ChangePasswordView(APIView):
    """
    POST /api/auth/change-password/
    Request body: old_password, new_password, confirm_new_password
    Blacklists all existing refresh tokens after a successful change.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        if not user.check_password(serializer.validated_data["old_password"]):
            return Response(
                {"error": "Old password is incorrect"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(serializer.validated_data["new_password"])
        user.save()

        # Invalidate all existing refresh tokens so other sessions are logged out
        _blacklist_all_user_tokens(user)

        return Response({"message": "Password changed successfully"}, status=status.HTTP_200_OK)


class ForgotPasswordView(APIView):
    """
    POST /api/auth/forgot-password/
    Request body: email
    If email exists, a reset link is printed in the terminal.
    """

    authentication_classes = []
    permission_classes     = [AllowAny]

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {"message": "If this email is registered, a password reset link has been sent. Check your terminal."},
            status=status.HTTP_200_OK,
        )


class ResetPasswordView(APIView):
    """
    POST /api/auth/reset-password/<uid>/<token>/
    Request body: password, confirm_password
    """

    authentication_classes = []
    permission_classes     = [AllowAny]

    def post(self, request, uid, token):
        serializer = ResetPasswordSerializer(
            data=request.data,
            context={"uid": uid, "token": token},
        )
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # FIXED: side effects moved out of validate() into the view
        user = serializer.validated_data["user"]
        user.set_password(serializer.validated_data["password"])
        user.save()

        return Response(
            {"message": "Password reset successfully. Please login."},
            status=status.HTTP_200_OK,
        )


# ── Profile views ─────────────────────────────────────────────────────────────

class UserProfileView(APIView):
    """
    GET    /api/users/me/  — returns logged-in user's profile.
    PATCH  /api/users/me/  — updates profile.
    DELETE /api/users/me/  — permanently deletes the logged-in user's own account.
                             Requires password confirmation in request body.
    """

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
        """
        DELETE /api/users/me/
        Permanently deletes the logged-in user's own account.

        Request body:
          { "password": "their_current_password" }

        Password confirmation is REQUIRED before deletion.
        This prevents accidental or unauthorised deletion if a session is left open.

        What gets deleted automatically (via CASCADE in models):
          - All blogs authored by this user
          - All comments posted by this user
          - All subscriptions (as subscriber and as author)
          - All notifications sent to this user
          - All notifications created by this user's blogs
        """
        password = request.data.get("password")

        if not password:
            return Response(
                {"error": "Password is required to delete your account."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not request.user.check_password(password):
            return Response(
                {"error": "Incorrect password."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        request.user.delete()
        return Response(
            {"message": "Your account has been permanently deleted."},
            status=status.HTTP_200_OK,
        )


class PublicAuthorProfileView(APIView):
    """
    GET /api/users/authors/<username>/
    Returns public author profile. Anyone can access it.
    """

    authentication_classes = []
    permission_classes     = [AllowAny]

    def get(self, request, username):
        user = User.objects.filter(
            username=username, role=User.ROLE_AUTHOR, is_active=True
        ).first()

        if not user:
            return Response({"error": "Author not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = PublicUserProfileSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)


# ── Subscription views ────────────────────────────────────────────────────────

class SubscribeAuthorView(APIView):
    """POST /api/users/subscribe/<username>/"""

    permission_classes = [IsAuthenticated]

    def post(self, request, username):
        author = User.objects.filter(
            username=username, role=User.ROLE_AUTHOR, is_active=True
        ).first()

        if not author:
            return Response({"error": "Author not found"}, status=status.HTTP_404_NOT_FOUND)

        if request.user == author:
            return Response({"error": "You cannot subscribe to yourself"}, status=status.HTTP_400_BAD_REQUEST)

        if Subscription.objects.is_subscribed(subscriber=request.user, author=author):
            return Response({"error": "Already subscribed"}, status=status.HTTP_400_BAD_REQUEST)

        Subscription.objects.create(subscriber=request.user, author=author)
        return Response({"message": f"Subscribed to {author.username}"}, status=status.HTTP_201_CREATED)


class UnsubscribeAuthorView(APIView):
    """DELETE /api/users/unsubscribe/<username>/"""

    permission_classes = [IsAuthenticated]

    def delete(self, request, username):
        author = User.objects.filter(
            username=username, role=User.ROLE_AUTHOR, is_active=True
        ).first()

        if not author:
            return Response({"error": "Author not found"}, status=status.HTTP_404_NOT_FOUND)

        subscription = Subscription.objects.filter(
            subscriber=request.user, author=author
        ).first()

        if not subscription:
            return Response({"error": "Not subscribed"}, status=status.HTTP_400_BAD_REQUEST)

        subscription.delete()
        return Response({"message": f"Unsubscribed from {author.username}"}, status=status.HTTP_200_OK)


class MySubscriptionsView(APIView):
    """GET /api/users/my-subscriptions/"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        subscriptions = Subscription.objects.filter(
            subscriber=request.user
        ).select_related("author")
        serializer = SubscriptionSerializer(subscriptions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


# ── Admin user management ─────────────────────────────────────────────────────

class AdminUserListView(APIView):
    """
    GET /api/admin/users/
    Returns list of all users. Only admin can access.
    """

    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        users = User.objects.all()
        serializer = UserProfileSerializer(users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class AdminUserDetailView(APIView):
    """
    GET    /api/admin/users/<user_id>/ — get user details
    PATCH  /api/admin/users/<user_id>/ — update role or active status
    DELETE /api/admin/users/<user_id>/ — delete user
    Admin cannot modify other admins or superadmins.
    """

    permission_classes = [IsAuthenticated, IsAdminUser]

    def _get_user(self, user_id):
        """Returns user or None."""
        return User.objects.filter(id=user_id).first()

    def _check_protected(self, user):
        """Return a 403 Response if the target user is protected, else None."""
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

        serializer = UserProfileSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, user_id):
        user = self._get_user(user_id)
        if not user:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        # FIXED: extracted shared guard into _check_protected()
        guard = self._check_protected(user)
        if guard:
            return guard

        serializer = AdminUserUpdateSerializer(user, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        serializer.save()
        return Response(UserProfileSerializer(user).data, status=status.HTTP_200_OK)

    def delete(self, request, user_id):
        user = self._get_user(user_id)
        if not user:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        # FIXED: extracted shared guard into _check_protected()
        guard = self._check_protected(user)
        if guard:
            return guard

        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ── Superadmin view ───────────────────────────────────────────────────────────

class AdminAccountCreateView(APIView):
    """
    POST /api/superadmin/create-admin/
    Only superadmin can create an admin account.
    Request body: email, username, password, confirm_password, first_name, last_name
    """

    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # FIXED: pass extra fields directly to save() instead of a second .save() call
        user = serializer.save(role=User.ROLE_ADMIN, is_staff=True, is_superadmin=False)

        return Response(
            {"message": "Admin account created successfully", "user_id": user.id},
            status=status.HTTP_201_CREATED,
        )