"""Back-office pages (/django-admin/) for developers and super admins.

Staff manage this data in the React staff dashboard later (M2.3 / M2.11).
"""

from django.contrib import admin

from .models import Intake, Programme, School


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
