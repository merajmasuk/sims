from django.contrib import admin

from .models import Application


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ("full_name", "email", "program", "status", "submitted_at")
    list_filter = ("status", "program")
    search_fields = ("first_name", "last_name", "email")
    readonly_fields = ("submitted_at", "created_at", "updated_at")
