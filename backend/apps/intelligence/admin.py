"""Back-office pages (/django-admin/). In the pilot this is where the operator reviews
groups and messages."""

from django.contrib import admin

from .models import Message, Source, SourceMember


class SourceMemberInline(admin.TabularInline):
    model = SourceMember
    extra = 0
    raw_id_fields = ("user",)


@admin.register(Source)
class SourceAdmin(admin.ModelAdmin):
    list_display = ("title", "platform", "status", "trust", "scope_confirmed", "joined_at")
    list_filter = ("platform", "status", "trust", "scope_confirmed")
    search_fields = ("title", "external_id")
    raw_id_fields = ("connected_by", "section")
    inlines = [SourceMemberInline]


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("sent_at", "source", "sender_name", "short_text", "triage")
    list_filter = ("triage", "source__platform", "source")
    search_fields = ("text", "sender_name")
    date_hierarchy = "sent_at"
    raw_id_fields = ("source", "reply_to")
    list_select_related = ("source",)

    @admin.display(description="Text")
    def short_text(self, message):
        return message.text[:80]
