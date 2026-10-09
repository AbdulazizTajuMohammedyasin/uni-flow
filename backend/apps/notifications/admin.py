"""Back-office page (/django-admin/): the alerts users received (read-only)."""

from django.contrib import admin

from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("created_at", "recipient", "kind", "title", "read_at")
    list_filter = ("kind",)
    search_fields = ("recipient__email", "title")
    list_select_related = ("recipient",)
    readonly_fields = [field.name for field in Notification._meta.fields]

    def has_add_permission(self, request):
        return False
