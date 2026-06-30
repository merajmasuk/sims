from django.contrib.auth.models import AbstractUser,BaseUserManager
from django.db import models
from uuid6 import uuid7


class UserManager(BaseUserManager):
    """
    Custom manager for the email-based User model.
    No username field exists, so createsuperuser and create_user
    must be driven by email instead.
    """

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("Users must have an email address.")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", User.Role.ADMIN)

        if not extra_fields.get("is_staff"):
            raise ValueError("Superuser must have is_staff=True.")
        if not extra_fields.get("is_superuser"):
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    """
   Custom user model for SIMS.

   - No `username` field; `email` is the USERNAME_FIELD.
   - `first_name` / `last_name` are kept (inherited from AbstractUser) so the
     data is structured where it's useful (e.g. sorting, official records),
     with `full_name` as a derived convenience property for UGC-style forms
     that expect a single name string.
   - `keycloak_uid` is the link to the Keycloak-issued JWT `sub` claim.
     This is how KeycloakJWTAuthentication resolves a token to a Django user.
   - Accounts are pre-provisioned only. A valid Keycloak JWT with no matching
     `keycloak_uid` here is NOT auto-created — see authentication.py.
   - `sso_provider` / `sso_uid` are nullable placeholders for a future
     non-Keycloak SSO path (e.g. Google Workspace). Unused for MVP.
   """

    class Role(models.TextChoices):
        ADMIN = "admin", "Admin"
        STUDENT = "student", "Student"
        FACULTY = "faculty", "Faculty"

    id = models.UUIDField(primary_key=True, default=uuid7, editable=False)

    username = None
    email = models.EmailField(unique=True)

    role = models.CharField(max_length=10, choices=list(Role.choices))

    keycloak_uid = models.CharField(
        max_length=255,
        unique=True,
        null=True,
        blank=True,
        db_index=True,
        help_text="Keycloak 'sub' claim. Null only for accounts not yet linked to Keycloak.",
    )

    sso_provider = models.CharField(max_length=20, null=True, blank=True)
    sso_uid = models.CharField(max_length=255, null=True, blank=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    objects = UserManager()

    class Meta:
        db_table = "users"
        ordering = ["first_name", "last_name"]

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"


class LoginAuditLog(models.Model):
    """
    Records login events only — not every authenticated request.
    A 'login event' is the first successful (or failed) authentication
    in a session, as determined by the authentication layer.

    `user` is nullable to support logging failed attempts where the
    keycloak_uid doesn't resolve to any known Django user (e.g. a valid
    Keycloak token for an account that was never pre-provisioned in SIMS).
    """

    class Action(models.TextChoices):
        LOGIN_FAILED = "login_failed", "Login failed"
        LOGIN_SUCCESS = "login_success", "Login success"
        TOKEN_EXPIRED = "token_expired", "Token expired"

    id = models.UUIDField(primary_key=True, default=uuid7, editable=False)

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="login_audit_logs",
    )
    keycloak_uid = models.CharField(
        max_length=255,
        help_text="Raw 'sub' claim from the JWT, recorded even if it doesn't match a User."
    )

    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    action = models.CharField(max_length=20, choices=list(Action.choices))

    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "login_audit_logs"
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["user", "-timestamp"]),
            models.Index(fields=["keycloak_uid", "-timestamp"]),
        ]

    def __str__(self):
        who = self.user.email if self.user else self.keycloak_uid
        return f"{self.action} - {who} @ {self.timestamp:%Y-%m-%d %H:%M}"
