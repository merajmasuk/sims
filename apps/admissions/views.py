from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from models import Application
from serializers import (
    ApplicationCreateSerializer,
    ApplicationReviewSerializer,
    ApplicationSerializer,
)
from services import convert_application_to_student

# Reuse the role-based permission classes already built in apps.users
from apps.users.permissions import IsAdminRole


class ApplicationViewSet(viewsets.ModelViewSet):
    """
    /api/admissions/applications/            GET (staff list), POST (public submit)
    /api/admissions/applications/{id}/        GET, PATCH, DELETE (staff)
    /api/admissions/applications/{id}/review/ POST — transition status
    /api/admissions/applications/{id}/convert/ POST — accepted -> Student
    """

    queryset = Application.objects.select_related("program", "reviewed_by").all()

    def get_serializer_class(self):
        if self.action == "create":
            return ApplicationCreateSerializer
        if self.action == "review":
            return ApplicationReviewSerializer
        return ApplicationSerializer

    def get_permissions(self):
        # Public application submission is open; everything else is admin-only.
        if self.action == "create":
            return [AllowAny()]
        return [IsAuthenticated(), IsAdminRole()]

    def perform_create(self, serializer):
        serializer.save(status=Application.Status.SUBMITTED)

    @action(detail=True, methods=["post"])
    def review(self, request, pk=None):
        application = self.get_object()
        serializer = ApplicationReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        application.status = serializer.validated_data["status"]
        application.notes = serializer.validated_data.get("notes", application.notes)
        application.reviewed_by = request.user
        application.reviewed_at = timezone.now()
        application.save(update_fields=["status", "notes", "reviewed_by", "reviewed_at", "updated_at"])

        return Response(ApplicationSerializer(application).data)

    @action(detail=True, methods=["post"])
    def convert(self, request, pk=None):
        application = self.get_object()
        admission_year = request.data.get("admission_year", timezone.now().year)

        if not application.is_convertible:
            return Response(
                {"detail": "Application must be accepted and not already converted."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            student = convert_application_to_student(application, admission_year=admission_year)
        except Exception as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)

        return Response({"student_id": str(student.id)}, status=status.HTTP_201_CREATED)
