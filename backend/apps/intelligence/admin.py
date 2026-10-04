"""Back-office pages (/django-admin/). In the pilot this is where the operator reviews
groups, messages and insights, and writes official staff posts."""

from django.contrib import admin
from django.db import models
from django.utils import timezone

from apps.audiences.models import Audience
from apps.publishing.services import archive, publish

from .models import Insight, InsightEvidence, Message, MessageFile, Source, SourceMember
from .tasks import triage_source

# Links typed without "https://" are read as https (Django 6.0's default, chosen now).
HTTPS_LINKS = {models.URLField: {"assume_scheme": "https"}}


class SourceMemberInline(admin.TabularInline):
    model = SourceMember
    extra = 0
    raw_id_fields = ("user",)


@admin.register(Source)
class SourceAdmin(admin.ModelAdmin):
    formfield_overrides = HTTPS_LINKS
    list_display = ("title", "platform", "status", "trust", "scope_confirmed", "joined_at")
    list_filter = ("platform", "status", "trust", "scope_confirmed")
    search_fields = ("title", "external_id")
    raw_id_fields = ("connected_by", "section")
    inlines = [SourceMemberInline]
    actions = ["sort_new_messages"]

    @admin.action(description="Sort new messages now (academic or noise)")
    def sort_new_messages(self, request, queryset):
        for source in queryset:
            triage_source.delay(source.id)
        self.message_user(request, f"Sorting started for {queryset.count()} group(s).")


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


@admin.register(MessageFile)
class MessageFileAdmin(admin.ModelAdmin):
    formfield_overrides = HTTPS_LINKS
    list_display = ("created_at", "kind", "original_name", "uploaded_by", "message", "size_bytes")
    list_filter = ("kind",)
    search_fields = ("original_name", "source_url")
    raw_id_fields = ("message", "uploaded_by")


class InsightEvidenceInline(admin.TabularInline):
    model = InsightEvidence
    extra = 0
    fields = ("message", "quote")
    readonly_fields = ("message", "quote")
    can_delete = False


@admin.register(Insight)
class InsightAdmin(admin.ModelAdmin):
    """AI findings and official staff posts. In the pilot, staff posts are written here:
    fill in the post, choose who it's for (leave empty for all students), save, then use
    the "Publish" action."""

    formfield_overrides = HTTPS_LINKS
    list_display = (
        "title",
        "kind",
        "status",
        "origin",
        "confidence",
        "publisher_type",
        "published_at",
    )
    list_filter = ("status", "origin", "kind", "publisher_type")
    search_fields = ("title", "summary")
    date_hierarchy = "created_at"
    fields = (
        "kind",
        "title",
        "summary",
        "importance",
        "action_required",
        "action_text",
        "info_type",
        "topics",
        "starts_at",
        "deadline_at",
        "location",
        "link",
        "audience",
        "publisher_type",
        "publisher_school",
        "expires_at",
        "status",
        "origin",
        "confidence",
        "publisher_source",
        "published_at",
        "created_by",
        "corrected_by",
        "corrected_at",
        "model_version",
        "data",
    )
    readonly_fields = (
        "status",
        "origin",
        "confidence",
        "publisher_source",
        "published_at",
        "created_by",
        "corrected_by",
        "corrected_at",
        "model_version",
        "data",
    )
    inlines = [InsightEvidenceInline]
    actions = ["publish_selected", "retract_selected"]

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields["audience"].required = False  # empty = all students
        form.base_fields["audience"].help_text = "Leave empty to send it to all students."
        return form

    def save_model(self, request, obj, form, change):
        if obj.audience_id is None:
            obj.audience = Audience.objects.create()  # all students
        if not change:
            obj.origin = Insight.Origin.STAFF
            obj.confidence = 1.0
            obj.created_by = request.user
        elif obj.origin == Insight.Origin.AI:
            obj.corrected_by = request.user  # a person fixed what the AI found
            obj.corrected_at = timezone.now()
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)

    @admin.action(description="Publish selected (students receive them)")
    def publish_selected(self, request, queryset):
        for insight in queryset:
            publish(insight, request.user)
        self.message_user(request, f"Published {queryset.count()} item(s).")

    @admin.action(description="Retract selected (take them back)")
    def retract_selected(self, request, queryset):
        for insight in queryset:
            archive(insight, request.user)
        self.message_user(request, f"Retracted {queryset.count()} item(s).")
