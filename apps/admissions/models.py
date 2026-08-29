import uuid6
from django.conf import settings
from django.db import models


class Application(models.Model):
    class Status(models.TextChoices):
        SUBMITTED = "submitted", "Submitted"
        UNDER_REVIEW = "under_review", "Under review"
        ACCEPTED = "accepted", "Accepted"
        REJECTED = "rejected", "Rejected"

    id = models.UUIDField(primary_key=True, default=uuid6.uuid7, editable=False)

    program = models.ForeignKey(
        "core.Program",
        on_delete=models.PROTECT,
        related_name="applications",
    )

    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    email = models.EmailField()
    phone = models.CharField(max_length=32)

    status = models.CharField(
        max_length=20,
        choices=list(Status.choices),
        default=Status.SUBMITTED,
    )
    notes = models.TextField(blank=True)

    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_applications",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "admissions"
        ordering = ["-submitted_at"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["email"]),
        ]

    def __str__(self):
        return f"{self.first_name} {self.last_name} — {self.program} ({self.status})"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def is_convertible(self):
        """Only an accepted application, not already converted, can become a Student."""
        return self.status == self.Status.ACCEPTED and not hasattr(self, "student")
