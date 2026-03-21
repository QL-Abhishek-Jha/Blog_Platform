import logging
from rest_framework.permissions import BasePermission

logger = logging.getLogger("api")


class IsSuperAdmin(BasePermission):
    def has_permission(self, request, view):
        granted = bool(
            request.user
            and request.user.is_authenticated
            and getattr(request.user, "is_superadmin", False) is True
        )
        if not granted:
            _log_denied("IsSuperAdmin", request)
        return granted


class IsAdminUser(BasePermission):
    def has_permission(self, request, view):
        granted = bool(
            request.user
            and request.user.is_authenticated
            and getattr(request.user, "role", None) == "admin"
        )
        if not granted:
            _log_denied("IsAdminUser", request)
        return granted


class IsAuthorUser(BasePermission):
    def has_permission(self, request, view):
        granted = bool(
            request.user
            and request.user.is_authenticated
            and getattr(request.user, "role", None) == "author"
        )
        if not granted:
            _log_denied("IsAuthorUser", request)
        return granted


class IsAuthorOrAdminUser(BasePermission):
    def has_permission(self, request, view):
        granted = bool(
            request.user
            and request.user.is_authenticated
            and getattr(request.user, "role", None) in ("author", "admin")
        )
        if not granted:
            _log_denied("IsAuthorOrAdminUser", request)
        return granted


def _log_denied(permission_name: str, request) -> None:
    user    = getattr(request, "user", None)
    user_id = getattr(user, "id", "anonymous") if user and user.is_authenticated else "anonymous"
    logger.warning(
        f"[PERMISSION DENIED] permission={permission_name} "
        f"user_id={user_id} "
        f"endpoint={request.get_full_path()} "
        f"method={request.method}"
    )