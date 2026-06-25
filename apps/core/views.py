from rest_framework import viewsets, mixins
from rest_framework.permissions import IsAuthenticated
from models import Department, Program, AcademicTerm
from serializers import DepartmentSerializer, ProgramSerializer, AcademicTermSerializer


class ReadOnlyViewSet(
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    """Base class for read-only viewsets. Full CRUD will be added post-MVP."""
    permission_classes = [IsAuthenticated]


class DepartmentViewSet(ReadOnlyViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer


class ProgramViewSet(ReadOnlyViewSet):
    queryset = Program.objects.select_related("department").all()
    serializer_class = ProgramSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        department_id = self.request.query_params.get("department")
        if department_id:
            qs = qs.filter(department_id=department_id)
        return qs


class AcademicTermViewSet(ReadOnlyViewSet):
    queryset = AcademicTerm.objects.all()
    serializer_class = AcademicTermSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        is_active = self.request.query_params.get("is_active")
        if is_active is not None:
            qs = qs.filter(is_active=is_active.lower() == "true")
        return qs
