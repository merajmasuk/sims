import uuid6
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("core", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Application",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid6.uuid7,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("first_name", models.CharField(max_length=150)),
                ("last_name", models.CharField(max_length=150)),
                ("email", models.EmailField(max_length=254)),
                ("phone", models.CharField(max_length=32)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("submitted", "Submitted"),
                            ("under_review", "Under review"),
                            ("accepted", "Accepted"),
                            ("rejected", "Rejected"),
                        ],
                        default="submitted",
                        max_length=20,
                    ),
                ),
                ("notes", models.TextField(blank=True)),
                ("reviewed_at", models.DateTimeField(blank=True, null=True)),
                ("submitted_at", models.DateTimeField(auto_now_add=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "program",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="applications",
                        to="core.program",
                    ),
                ),
                (
                    "reviewed_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="reviewed_applications",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["-submitted_at"],
            },
        ),
        migrations.AddIndex(
            model_name="application",
            index=models.Index(fields=["status"], name="admissions__status_idx"),
        ),
        migrations.AddIndex(
            model_name="application",
            index=models.Index(fields=["email"], name="admissions__email_idx"),
        ),
    ]
