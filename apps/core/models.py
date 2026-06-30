import uuid6
from django.db import models
from django.core.exceptions import ValidationError


def generate_uuid7():
    """Generate a UUID7 (time-ordered) primary key."""
    return uuid6.uuid7()


class Department(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=generate_uuid7,
        editable=False,
    )
    name = models.CharField(max_length=255, unique=True)
    code = models.CharField(
        max_length=20,
        unique=True,
        help_text="Short uppercase identifier, e.g. CSE, BBA.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Department"
        verbose_name_plural = "Departments"

    def save(self, *args, **kwargs):
        self.code = self.code.upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.code} — {self.name}"


class Program(models.Model):
    class SemesterSystem(models.TextChoices):
        BI = "bi", "Bi-Semester"
        TRI = "tri", "Tri-Semester"
        YEARLY = "yearly", "Yearly"

    id = models.UUIDField(
        primary_key=True,
        default=generate_uuid7,
        editable=False,
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.PROTECT,
        related_name="programs",
    )
    name = models.CharField(max_length=255)
    code = models.CharField(
        max_length=20,
        unique=True,
        help_text="Internal program code, e.g. BSC-CSE.",
    )
    ugc_program_code = models.CharField(
        max_length=5,
        unique=True,
        help_text="5-digit UGC program code. Stored as string to preserve leading zeros.",
    )
    duration_years = models.PositiveSmallIntegerField(
        help_text="Total program duration in years, e.g. 4.",
    )
    semester_system = models.CharField(
        max_length=10,
        choices=list(SemesterSystem.choices),
        default=SemesterSystem.BI,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Program"
        verbose_name_plural = "Programs"

    def clean(self):
        if self.ugc_program_code and not self.ugc_program_code.isdigit():
            raise ValidationError(
                {"ugc_program_code": "UGC program code must contain digits only."}
            )
        if self.ugc_program_code and len(self.ugc_program_code) != 5:
            raise ValidationError(
                {"ugc_program_code": "UGC program code must be exactly 5 digits."}
            )

    def __str__(self):
        return f"{self.code} — {self.name}"


class AcademicTerm(models.Model):
    class TermType(models.TextChoices):
        SPRING = "spring", "Spring"
        SUMMER = "summer", "Summer"
        FALL = "fall", "Fall"

    # Fixed mapping: term_type → semester number.
    # spring=1, summer=2, fall=3 regardless of semester system.
    # Bi-semester programs will naturally produce sequences 1, 3, 1, 3 …
    # (semester 2 simply never appears for bi-semester students).
    SEMESTER_NUMBER_MAP = {
        TermType.SPRING: 1,
        TermType.SUMMER: 2,
        TermType.FALL: 3,
    }

    id = models.UUIDField(
        primary_key=True,
        default=generate_uuid7,
        editable=False,
    )
    name = models.CharField(
        max_length=100,
        help_text="Human-readable label, e.g. 'Spring 2026'.",
    )
    term_type = models.CharField(
        max_length=10,
        choices=list(TermType.choices),
    )
    year = models.PositiveIntegerField()
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(
        default=False,
        help_text="Multiple terms may be active simultaneously.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-year", "term_type"]
        verbose_name = "Academic Term"
        verbose_name_plural = "Academic Terms"
        constraints = [
            models.UniqueConstraint(
                fields=["year", "term_type"],
                name="unique_term_per_year",
            )
        ]

    def clean(self):
        if self.start_date and self.end_date:
            if self.end_date <= self.start_date:
                raise ValidationError(
                    {"end_date": "End date must be after start date."}
                )

    @property
    def semester_number(self):
        """
        Derive semester number from term_type.
        spring → 1, summer → 2, fall → 3.
        Not stored in DB — computed on demand.
        """
        return self.SEMESTER_NUMBER_MAP.get(self.term_type)

    def __str__(self):
        return self.name
    