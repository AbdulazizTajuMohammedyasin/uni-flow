"""Back-office pages (/django-admin/) for developers and super admins.

In the pilot this is where courses and terms are added and fixed (React pages come after the pilot).
"""

from django.contrib import admin
from django.utils import timezone

from .models import Course, Intake, Programme, School, Term


@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name", "code")


@admin.register(Programme)
class ProgrammeAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "school", "level", "is_active")
    list_filter = ("level", "is_active", "school")
    search_fields = ("name", "code")
    list_select_related = ("school",)


@admin.register(Intake)
class IntakeAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "start_date", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name", "code")


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "school", "is_active")
    list_filter = ("is_active", "school")
    search_fields = ("code", "name")
    list_select_related = ("school",)


@admin.register(Term)
class TermAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "calendar",
        "academic_session",
        "number",
        "starts_on",
        "ends_on",
        "is_current_now",
    )
    list_filter = ("calendar", "academic_session")

    @admin.display(boolean=True, description="Current now")
    def is_current_now(self, term):
        current = Term.current(term.calendar, timezone.localdate())
        return current is not None and current.pk == term.pk
