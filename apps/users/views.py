from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

from .models import User, Subscription
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


# AUTH VIEWS

class UserRegistrationView(APIView):
    """
    POST /api/auth/register/
    This API registers a new user.
    Anyone can access it.

    Request body:
    username, email, password, confirm_password, first_name, last_name
    """

    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.save()

        return Response(
            {
                "message": "Registration successful",
                "user_id": user.id
            },
            status=status.HTTP_201_CREATED
        )


class UserLoginView(APIView):
    """
    POST /api/auth/login/
    Used for user login.

    Anyone can access it.

    Request body:
    email, password

    Response:
    access_token and refresh_token
    """

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
                    "role": user.role
                }
            },
            status=status.HTTP_200_OK
        )


class TokenRefreshView(APIView):
    """
    POST /api/auth/token/refresh/

    Used to generate new access and refresh tokens
    when the access token expires.

    Request body:
    refresh_token
    """

    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):

        refresh_token = request.data.get("refresh_token")

        if not refresh_token:
            return Response(
                {"error": "refresh_token is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:

            old_refresh = RefreshToken(refresh_token)

            user_id = old_refresh.payload.get("user_id")

            user = User.objects.filter(id=user_id).first()

            if not user:
                return Response(
                    {"error": "User not found. Please login again."},
                    status=status.HTTP_401_UNAUTHORIZED
                )

            old_refresh.blacklist()

            new_refresh = RefreshToken.for_user(user)

            return Response(
                {
                    "access_token": str(new_refresh.access_token),
                    "refresh_token": str(new_refresh),
                    "user": {
                        "id": user.id,
                        "email": user.email,
                        "role": user.role
                    }
                },
                status=status.HTTP_200_OK
            )

        except TokenError:

            return Response(
                {
                    "error": "Refresh token is expired. Please login again.",
                    "code": "token_expired"
                },
                status=status.HTTP_401_UNAUTHORIZED
            )


class UserLogoutView(APIView):
    """
    POST /api/auth/logout/

    Used to logout a user.
    Requires authentication.

    Request body:
    refresh_token
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):

        refresh_token = request.data.get("refresh_token")

        if not refresh_token:
            return Response(
                {"error": "refresh_token is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:

            token = RefreshToken(refresh_token)
            token.blacklist()

        except TokenError:

            return Response(
                {"error": "Token is invalid or expired"},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            {"message": "Logged out successfully"},
            status=status.HTTP_200_OK
        )


class ChangePasswordView(APIView):
    """
    POST /api/auth/change-password/

    Used to change password.
    User must be logged in.

    Request body:
    old_password
    new_password
    confirm_new_password
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
                status=status.HTTP_400_BAD_REQUEST
            )

        user.set_password(serializer.validated_data["new_password"])
        user.save()

        return Response(
            {"message": "Password changed successfully"},
            status=status.HTTP_200_OK
        )


class ForgotPasswordView(APIView):
    """
    POST /api/auth/forgot-password/

    Used when user forgets password.

    Request body:
    email

    If the email exists, a reset link is printed in the terminal.
    """

    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):

        serializer = ForgotPasswordSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {
                "message": "If this email is registered, a password reset link has been sent. Check your terminal."
            },
            status=status.HTTP_200_OK
        )


class ResetPasswordView(APIView):
    """
    POST /api/auth/reset-password/<uid>/<token>/

    Used to reset password after clicking reset link.

    Request body:
    password
    confirm_password
    """

    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request, uid, token):

        serializer = ResetPasswordSerializer(
            data=request.data,
            context={"uid": uid, "token": token}
        )

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {"message": "Password reset successfully. Please login."},
            status=status.HTTP_200_OK
        )


# PROFILE VIEWS

class UserProfileView(APIView):
    """
    GET /api/users/me/
    Returns logged in user's profile.

    PATCH /api/users/me/
    Used to update profile.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):

        serializer = UserProfileSerializer(request.user)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request):

        serializer = UserProfileSerializer(
            request.user,
            data=request.data,
            partial=True
        )

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        serializer.save()

        return Response(serializer.data, status=status.HTTP_200_OK)


class PublicAuthorProfileView(APIView):
    """
    GET /api/users/authors/<username>/

    Returns public author profile.
    Anyone can access it.
    """

    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request, username):

        user = User.objects.filter(
            username=username,
            role="author",
            is_active=True
        ).first()

        if not user:
            return Response(
                {"error": "Author not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = PublicUserProfileSerializer(user)

        return Response(serializer.data, status=status.HTTP_200_OK)


# SUBSCRIPTION VIEWS

class SubscribeAuthorView(APIView):
    """
    POST /api/users/subscribe/<username>/

    Used to subscribe to an author.
    User must be logged in.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, username):

        author = User.objects.filter(
            username=username,
            role="author",
            is_active=True
        ).first()

        if not author:
            return Response(
                {"error": "Author not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        if request.user == author:

            return Response(
                {"error": "You cannot subscribe to yourself"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if Subscription.objects.is_subscribed(
                subscriber=request.user,
                author=author):

            return Response(
                {"error": "Already subscribed"},
                status=status.HTTP_400_BAD_REQUEST
            )

        Subscription.objects.create(
            subscriber=request.user,
            author=author
        )

        return Response(
            {"message": f"Subscribed to {author.username}"},
            status=status.HTTP_201_CREATED
        )


class UnsubscribeAuthorView(APIView):
    """
    DELETE /api/users/unsubscribe/<username>/

    Used to unsubscribe from an author.
    """

    permission_classes = [IsAuthenticated]

    def delete(self, request, username):

        author = User.objects.filter(
            username=username,
            role="author",
            is_active=True
        ).first()

        if not author:
            return Response(
                {"error": "Author not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        subscription = Subscription.objects.filter(
            subscriber=request.user,
            author=author
        ).first()

        if not subscription:
            return Response(
                {"error": "Not subscribed"},
                status=status.HTTP_400_BAD_REQUEST
            )

        subscription.delete()

        return Response(
            {"message": f"Unsubscribed from {author.username}"},
            status=status.HTTP_200_OK
        )


class MySubscriptionsView(APIView):
    """
    GET /api/users/my-subscriptions/

    Returns list of authors the user subscribed to.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):

        subscriptions = Subscription.objects.filter(
            subscriber=request.user
        ).select_related("author")

        serializer = SubscriptionSerializer(
            subscriptions,
            many=True
        )

        return Response(serializer.data, status=status.HTTP_200_OK)


# ADMIN USER MANAGEMENT

class AdminUserListView(APIView):
    """
    GET /api/admin/users/

    Returns list of all users.
    Only admin can access.
    """

    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):

        users = User.objects.all()

        serializer = UserProfileSerializer(users, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)


class AdminUserDetailView(APIView):
    """
    GET /api/admin/users/<user_id>/
    Returns details of a user.

    PATCH /api/admin/users/<user_id>/
    Admin can change role or activate/deactivate user.

    DELETE /api/admin/users/<user_id>/
    Admin can delete a user.

    Admin cannot modify other admins or superadmins.
    """

    permission_classes = [IsAuthenticated, IsAdminUser]

    def _get_user(self, user_id):
        return User.objects.filter(id=user_id).first()

    def get(self, request, user_id):

        user = self._get_user(user_id)

        if not user:
            return Response(
                {"error": "User not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = UserProfileSerializer(user)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, user_id):

        user = self._get_user(user_id)

        if not user:
            return Response(
                {"error": "User not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        if user.role == "admin" or user.is_superadmin:

            return Response(
                {"error": "Cannot modify admin or superadmin accounts"},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = AdminUserUpdateSerializer(
            user,
            data=request.data,
            partial=True
        )

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        serializer.save()

        return Response(
            UserProfileSerializer(user).data,
            status=status.HTTP_200_OK
        )

    def delete(self, request, user_id):

        user = self._get_user(user_id)

        if not user:
            return Response(
                {"error": "User not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        if user.role == "admin" or user.is_superadmin:

            return Response(
                {"error": "Cannot delete admin or superadmin accounts"},
                status=status.HTTP_403_FORBIDDEN
            )

        user.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)


# SUPERADMIN VIEW

class AdminAccountCreateView(APIView):
    """
    POST /api/superadmin/create-admin/

    Only superadmin can create an admin account.

    Request body:
    email, username, password, confirm_password, first_name, last_name
    """

    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def post(self, request):

        serializer = UserRegistrationSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.save()

        user.role = "admin"
        user.is_staff = True
        user.is_superadmin = False

        user.save(update_fields=["role", "is_staff", "is_superadmin"])

        return Response(
            {
                "message": "Admin account created successfully",
                "user_id": user.id
            },
            status=status.HTTP_201_CREATED
        )