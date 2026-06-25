from rest_framework import serializers
from models import Department, Program, AcademicTerm


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ["id", "name", "code"]


class ProgramSerializer(serializers.ModelSerializer):
    department = DepartmentSerializer(read_only=True)

    class Meta:
        model = Program
        fields = [
            "id",
            "department",
            "name",
            "code",
            "ugc_program_code",
            "duration_years",
            "semester_system",
        ]


class AcademicTermSerializer(serializers.ModelSerializer):
    semester_number = serializers.IntegerField(read_only=True)

    class Meta:
        model = AcademicTerm
        fields = [
            "id",
            "name",
            "term_type",
            "year",
            "semester_number",
            "start_date",
            "end_date",
            "is_active",
        ]
