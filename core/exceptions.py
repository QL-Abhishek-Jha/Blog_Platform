from rest_framework.exceptions import APIException
from rest_framework import status


class AppException(APIException):
    status_code    = 400
    default_detail = "An application error occurred."
    default_code   = "app_error"

    def __init__(self, detail=None, status_code=None):
        if status_code is not None:
            self.status_code = status_code
        super().__init__(detail=detail or self.default_detail)


class InvalidCredentials(AppException):
    status_code    = status.HTTP_401_UNAUTHORIZED
    default_detail = "Invalid credentials."
    default_code   = "invalid_credentials"


class TokenExpired(AppException):
    status_code    = status.HTTP_401_UNAUTHORIZED
    default_detail = "Token has expired. Please login again."
    default_code   = "token_expired"


class TokenInvalid(AppException):
    status_code    = status.HTTP_401_UNAUTHORIZED
    default_detail = "Token is invalid."
    default_code   = "token_invalid"


class ResourceNotFound(AppException):
    status_code    = status.HTTP_404_NOT_FOUND
    default_detail = "Resource not found."
    default_code   = "not_found"


class UserNotFound(ResourceNotFound):
    default_detail = "User not found."
    default_code   = "user_not_found"


class AuthorNotFound(ResourceNotFound):
    default_detail = "Author not found."
    default_code   = "author_not_found"


class TopicNotFound(ResourceNotFound):
    default_detail = "Topic not found."
    default_code   = "topic_not_found"


class BlogNotFound(ResourceNotFound):
    default_detail = "Blog not found."
    default_code   = "blog_not_found"


class CommentNotFound(ResourceNotFound):
    default_detail = "Comment not found."
    default_code   = "comment_not_found"


class NotificationNotFound(ResourceNotFound):
    default_detail = "Notification not found."
    default_code   = "notification_not_found"


class PermissionDenied(AppException):
    status_code    = status.HTTP_403_FORBIDDEN
    default_detail = "You do not have permission to perform this action."
    default_code   = "permission_denied"


class ProtectedAccount(PermissionDenied):
    default_detail = "Cannot modify admin or superadmin accounts."
    default_code   = "protected_account"


class SelfSubscribe(AppException):
    status_code    = status.HTTP_400_BAD_REQUEST
    default_detail = "You cannot subscribe to yourself."
    default_code   = "self_subscribe"


class AlreadySubscribed(AppException):
    status_code    = status.HTTP_400_BAD_REQUEST
    default_detail = "Already subscribed to this author."
    default_code   = "already_subscribed"


class NotSubscribed(AppException):
    status_code    = status.HTTP_400_BAD_REQUEST
    default_detail = "You are not subscribed to this author."
    default_code   = "not_subscribed"