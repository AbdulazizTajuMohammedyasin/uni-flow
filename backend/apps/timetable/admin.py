"""Back-office pages (/django-admin/). In the pilot this is where sections and weekly
classes are added and fixed."""

from django.contrib import admin

from .models import (
    ClassChange,
    ClassChangeConfirmation,
    ClassMeeting,
    CourseSection,
    SectionEnrollment,
)


class ClassMeetingInline(admin.TabularInline):
    model = ClassMeeting
    extra = 1
    exclude = ("updated_by",)


@admin.register(CourseSection)
class CourseSectionAdmin(admin.ModelAdmin):
    list_display = ("course", "code", "term", "lecturer_name", "source", "is_active")
    list_filter = ("term", "source", "is_active", "course__school")
    search_fields = ("course__code", "course__name", "code", "lecturer_name")
    list_select_related = ("course", "term")
    autocomplete_fields = ("course",)
    readonly_fields = ("created_by", "updated_by")
    inlines = [ClassMeetingInline]

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(SectionEnrollment)
class SectionEnrollmentAdmin(admin.ModelAdmin):
    list_display = ("user", "section")
    list_filter = ("section__term",)
    search_fields = ("user__email", "section__course__code")
    list_select_related = ("user", "section__course", "section__term")
    autocomplete_fields = ("section",)
    raw_id_fields = ("user",)


class ClassChangeConfirmationInline(admin.TabularInline):
    model = ClassChangeConfirmation
    extra = 0
    can_delete = False
    readonly_fields = ("user", "status", "decided_at")

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(ClassChange)
class ClassChangeAdmin(admin.ModelAdmin):
    """Changes the AI proposed (read-only: publish or retract the insight instead)."""

    list_display = ("date", "kind", "section", "new_start", "new_room", "status", "insight")
    list_filter = ("kind", "status")
    search_fields = ("section__course__code", "insight__title")
    list_select_related = ("section__course", "section__term", "insight")
    readonly_fields = [field.name for field in ClassChange._meta.fields]
    inlines = [ClassChangeConfirmationInline]

    def has_add_permission(self, request):
        return False
