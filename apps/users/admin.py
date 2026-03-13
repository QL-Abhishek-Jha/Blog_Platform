from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, PasswordResetToken, Subscription

# CUSTOM ADMIN FOR ADMIN ROLE (non-superuser)
# Admins can change user role to "author" but cannot create other admins.
@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display  = ["id", "email", "username", "role", "is_active", "is_staff", "created_at"]
    list_filter   = ["role", "is_active", "is_staff"]
    search_fields = ["email", "username"]
    ordering      = ["-created_at"]

    # Fields shown when EDITING an existing user 
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal Info", {"fields": ("username", "first_name", "last_name", "bio", "profile_pic")}),
        ("Permissions", {"fields": ("role", "is_active", "is_staff", "is_superadmin", "groups", "user_permissions")}),
    )

    # Fields shown when CREATING a new user 
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "username", "password1", "password2", "role"),
        }),
    )

    def get_fieldsets(self, request, obj=None):
        """
        Superuser sees all fields.
        Admin (is_staff but not is_superadmin) sees limited fields — cannot assign admin role
        or change superadmin/staff flags.
        """
        if request.user.is_superadmin:
            return self.fieldsets
        # Non-superuser admin: hide dangerous permission fields
        return (
            (None, {"fields": ("email", "password")}),
            ("Personal Info", {"fields": ("username", "first_name", "last_name", "bio", "profile_pic")}),
            ("Permissions", {"fields": ("role", "is_active")}),
        )

    def formfield_for_choice_field(self, db_field, request, **kwargs):
        """
        Non-superuser admins can only set role to 'user' or 'author' — not 'admin'.
        """
        if db_field.name == "role" and not request.user.is_superadmin:
            kwargs["choices"] = (
                ("user", "User"),
                ("author", "Author"),
            )
        return super().formfield_for_choice_field(db_field, request, **kwargs)

    def has_delete_permission(self, request, obj=None):
        """Only superuser can delete users from panel."""
        return request.user.is_superadmin


@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "used", "expires_at", "created_at"]
    list_filter  = ["used"]


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display  = ["id", "subscriber", "author", "created_at"]
    list_filter   = ["created_at"]
    search_fields = ["subscriber__username", "author__username"]