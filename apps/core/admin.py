from django.contrib import admin
from models import Department, Program, AcademicTerm


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "created_at"]
    search_fields = ["name", "code"]
    ordering = ["code"]
    readonly_fields = ["id", "created_at", "updated_at"]
    fieldsets = [
        (None, {
            "fields": ["id", "name", "code"],
        }),
        ("Timestamps", {
            "fields": ["created_at", "updated_at"],
            "classes": ["collapse"],
        }),
    ]


@admin.register(Program)
class ProgramAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "department", "ugc_program_code", "semester_system", "duration_years"]
    list_filter = ["semester_system", "department"]
    search_fields = ["name", "code", "ugc_program_code"]
    ordering = ["code"]
    readonly_fields = ["id", "created_at", "updated_at"]
    autocomplete_fields = ["department"]
    fieldsets = [
        (None, {
            "fields": ["id", "department", "name", "code"],
        }),
        ("UGC & Academic Configuration", {
            "fields": ["ugc_program_code", "duration_years", "semester_system"],
        }),
        ("Timestamps", {
            "fields": ["created_at", "updated_at"],
            "classes": ["collapse"],
        }),
    ]


@admin.register(AcademicTerm)
class AcademicTermAdmin(admin.ModelAdmin):
    list_display = ["name", "term_type", "year", "semester_number", "start_date", "end_date", "is_active"]
    list_filter = ["term_type", "year", "is_active"]
    search_fields = ["name"]
    ordering = ["-year", "term_type"]
    readonly_fields = ["id", "semester_number", "created_at", "updated_at"]
    fieldsets = [
        (None, {
            "fields": ["id", "name", "term_type", "year"],
        }),
        ("Schedule", {
            "fields": ["start_date", "end_date", "is_active"],
        }),
        ("Derived", {
            "fields": ["semester_number"],
            "description": "semester_number is derived from term_type and never stored.",
        }),
        ("Timestamps", {
            "fields": ["created_at", "updated_at"],
            "classes": ["collapse"],
        }),
    ]
