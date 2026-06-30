import django.contrib.auth.models
import django.contrib.auth.validators
import django.utils.timezone
import uuid6
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.CreateModel(
            name="User",
            fields=[
                ("id", models.UUIDField(default=uuid6.uuid7, editable=False, primary_key=True, serialize=False)),
                ("password", models.CharField(max_length=128, verbose_name="password")),
                ("last_login", models.DateTimeField(blank=True, null=True, verbose_name="last login")),
                (
                    "is_superuser",
                    models.BooleanField(
                        default=False,
                        help_text="Designates that this user has all permissions without explicitly assigning them.",
                        verbose_name="superuser status",
                    ),
                ),
                ("first_name", models.CharField(blank=True, max_length=150, verbose_name="first name")),
                ("last_name", models.CharField(blank=True, max_length=150, verbose_name="last name")),
                (
                    "is_staff",
                    models.BooleanField(
                        default=False,
                        help_text="Designates whether the user can log into this admin site.",
                        verbose_name="staff status",
                    ),
                ),
                (
                    "is_active",
                    models.BooleanField(
                        default=True,
                        help_text="Designates whether this user should be treated as active. Unselect this instead of deleting accounts.",
                        verbose_name="active",
                    ),
                ),
                ("date_joined", models.DateTimeField(default=django.utils.timezone.now, verbose_name="date joined")),
                ("email", models.EmailField(max_length=254, unique=True)),
                (
                    "role",
                    models.CharField(
                        choices=[("admin", "Admin"), ("student", "Student"), ("faculty", "Faculty")],
                        max_length=20,
                    ),
                ),
                (
                    "keycloak_uid",
                    models.CharField(
                        blank=True,
                        db_index=True,
                        help_text="Keycloak 'sub' claim. Null only for accounts not yet linked to Keycloak.",
                        max_length=255,
                        null=True,
                        unique=True,
                    ),
                ),
                ("sso_provider", models.CharField(blank=True, max_length=50, null=True)),
                ("sso_uid", models.CharField(blank=True, max_length=255, null=True)),
                (
                    "groups",
                    models.ManyToManyField(
                        blank=True,
                        help_text="The groups this user belongs to. A user will get all permissions granted to each of their groups.",
                        related_name="user_set",
                        related_query_name="user",
                        to="auth.group",
                        verbose_name="groups",
                    ),
                ),
                (
                    "user_permissions",
                    models.ManyToManyField(
                        blank=True,
                        help_text="Specific permissions for this user.",
                        related_name="user_set",
                        related_query_name="user",
                        to="auth.permission",
                        verbose_name="user permissions",
                    ),
                ),
            ],
            options={
                "db_table": "users",
                "ordering": ["last_name", "first_name"],
            },
            managers=[
                ("objects", django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name="LoginAuditLog",
            fields=[
                ("id", models.UUIDField(default=uuid6.uuid7, editable=False, primary_key=True, serialize=False)),
                (
                    "keycloak_uid",
                    models.CharField(
                        help_text="Raw 'sub' claim from the JWT, recorded even if it doesn't match a User.",
                        max_length=255,
                    ),
                ),
                ("ip_address", models.GenericIPAddressField()),
                ("user_agent", models.TextField(blank=True)),
                (
                    "action",
                    models.CharField(
                        choices=[
                            ("login_success", "Login Success"),
                            ("login_failed", "Login Failed"),
                            ("token_expired", "Token Expired"),
                        ],
                        max_length=20,
                    ),
                ),
                ("timestamp", models.DateTimeField(auto_now_add=True)),
                (
                    "user",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="login_audit_logs",
                        to="users.user",
                    ),
                ),
            ],
            options={
                "db_table": "login_audit_logs",
                "ordering": ["-timestamp"],
            },
        ),
        migrations.AddIndex(
            model_name="loginauditlog",
            index=models.Index(fields=["user", "-timestamp"], name="login_audit_user_ts_idx"),
        ),
        migrations.AddIndex(
            model_name="loginauditlog",
            index=models.Index(fields=["keycloak_uid", "-timestamp"], name="login_audit_kcuid_ts_idx"),
        ),
    ]
