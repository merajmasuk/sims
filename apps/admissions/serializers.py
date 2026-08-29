from rest_framework import serializers

from .models import Application


class ApplicationSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = Application
        fields = [
            "id",
            "program",
            "first_name",
            "last_name",
            "full_name",
            "email",
            "phone",
            "status",
            "notes",
            "reviewed_by",
            "reviewed_at",
            "submitted_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "status",
            "reviewed_by",
            "reviewed_at",
            "submitted_at",
            "created_at",
            "updated_at",
        ]


class ApplicationCreateSerializer(serializers.ModelSerializer):
    """Public-facing serializer — applicants can only set their own submission fields."""

    class Meta:
        model = Application
        fields = ["program", "first_name", "last_name", "email", "phone"]


class ApplicationReviewSerializer(serializers.Serializer):
    """Used by the review action — staff-only, transitions status."""

    status = serializers.ChoiceField(
        choices=[Application.Status.UNDER_REVIEW, Application.Status.ACCEPTED, Application.Status.REJECTED]
    )
    notes = serializers.CharField(required=False, allow_blank=True)
