# apps/users/backends.py
from mozilla_django_oidc.auth import OIDCAuthenticationBackend
from apps.users.models import User

class KeycloakOIDCBackend(OIDCAuthenticationBackend):
    def get_or_create_user(self, access_token, id_token, payload):
        keycloak_uid = payload.get("sub")
        roles = payload.get("realm_access", {}).get("roles", [])

        user, created = User.objects.get_or_create(
            keycloak_uid=keycloak_uid,
            defaults={
                "email": payload.get("email", ""),
                "first_name": payload.get("given_name", ""),
                "last_name": payload.get("family_name", ""),
                "sso_provider": "keycloak",
            },
        )

        is_admin = "admin" in roles
        if user.is_staff != is_admin or user.is_superuser != is_admin:
            user.is_staff = is_admin
            user.is_superuser = is_admin
            user.save(update_fields=["is_staff", "is_superuser"])

        if not is_admin:
            return None  # reject non-admins from reaching /admin/ at all

        return user
