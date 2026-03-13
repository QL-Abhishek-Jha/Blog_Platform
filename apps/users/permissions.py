from rest_framework.permissions import BasePermission


class IsSuperAdmin(BasePermission):
    "Only the developer superadmin can access."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_superadmin is True
        )


class IsAdminUser(BasePermission):
    "Only users with role = admin can access."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == "admin"
        )


class IsAuthorUser(BasePermission):
    "Only users with role = author can access."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == "author"
        )


class IsAuthorOrAdminUser(BasePermission):
    "Authors and Admins can access."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role in ("author", "admin")
        )