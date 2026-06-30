from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from users.models import User, LoginAuditLog


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    """
    Admin for the custom User model. Pre-provisioning of accounts (before
    Keycloak linkage) happens here for MVP — no self-service registration.
    """

    model = User
    ordering = ("last_name", "first_name")
    list_display = ["email", "full_name", "role", "keycloak_uid", "is_active", "is_staff"]
    list_filter = ["role", "is_active", "is_staff"]
    search_fields = ["email", "first_name", "last_name", "keycloak_uid"]
    readonly_fields = ["email", "date_joined", "last_login"]

    fieldsets = (
        (None, {"fields": ("id", "email", "password")}),
        ("Personal info", {"fields": ("first_name", "last_name")}),
        ("Role & SSO", {"fields": ("role", "keycloak_uid", "sso_provider", "sso_uid")}),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "first_name",
                    "last_name",
                    "role",
                    "keycloak_uid",
                    "password1",
                    "password2",
                ),
            },
        ),
    )


@admin.register(LoginAuditLog)
class LoginAuditLogAdmin(admin.ModelAdmin):
    list_display = ["timestamp", "action", "user", "keycloak_uid", "ip_address"]
    list_filter = ["action"]
    search_fields = ["user__email", "keycloak_uid", "ip_address"]
    readonly_fields = [f.name for f in LoginAuditLog._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
