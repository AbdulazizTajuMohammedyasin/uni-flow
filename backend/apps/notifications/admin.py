"""Back-office pages (/django-admin/): the alerts users received and their phones (read-only)."""

from django.contrib import admin

from .models import Device, Notification, PushSettings


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("created_at", "recipient", "kind", "title", "read_at")
    list_filter = ("kind",)
    search_fields = ("recipient__email", "title")
    list_select_related = ("recipient",)
    readonly_fields = [field.name for field in Notification._meta.fields]

    def has_add_permission(self, request):
        return False


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ("user", "platform", "app_version", "is_active", "last_seen_at")
    list_filter = ("platform", "is_active", "deactivated_reason")
    search_fields = ("user__email",)
    list_select_related = ("user",)
    exclude = ("expo_token",)  # a personal address: not shown in the admin
    readonly_fields = [f.name for f in Device._meta.fields if f.name != "expo_token"]

    def has_add_permission(self, request):
        return False


@admin.register(PushSettings)
class PushSettingsAdmin(admin.ModelAdmin):
    list_display = ("user", "class_changes", "needs_you", "daily_digest")
    search_fields = ("user__email",)
    list_select_related = ("user",)
    readonly_fields = [field.name for field in PushSettings._meta.fields]

    def has_add_permission(self, request):
        return False
