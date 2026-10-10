"""Back-office pages (/django-admin/). In the pilot this is where the operator reviews
groups, messages and insights, and writes official staff posts."""

from django.contrib import admin
from django.db import models
from django.utils import timezone

from apps.audiences.models import Audience
from apps.publishing.models import Status

from . import services
from .models import (
    AICall,
    Delivery,
    DraftInsight,
    ExcludedSender,
    Insight,
    InsightEvidence,
    InsightMention,
    Message,
    MessageFile,
    Source,
    SourceMember,
    TimetableImport,
)
from .tasks import triage_source

# No "date_hierarchy" (the year/month/day bar): on MySQL it needs the time-zone tables, which
# a Windows MySQL install usually lacks, and the page then crashes. Date filters ("Today",
# "Past 7 days", "This month") in list_filter work everywhere.

# Links typed without "https://" are read as https (Django 6.0's default, chosen now).
HTTPS_LINKS = {models.URLField: {"assume_scheme": "https"}}


class SourceMemberInline(admin.TabularInline):
    model = SourceMember
    extra = 0
    raw_id_fields = ("user",)


@admin.register(Source)
class SourceAdmin(admin.ModelAdmin):
    """Groups. Review new ones: what they are for (the scope students suggested), whether
    they are official, and disconnect any that aren't academic."""

    formfield_overrides = HTTPS_LINKS
    list_display = (
        "title",
        "platform",
        "status",
        "trust",
        "scope_confirmed",
        "member_count",
        "message_count",
        "connected_by",
        "created_at",
    )
    list_filter = ("platform", "status", "trust", "scope_confirmed")
    search_fields = ("title", "external_id")
    raw_id_fields = ("connected_by", "section")
    list_select_related = ("connected_by",)
    inlines = [SourceMemberInline]
    actions = [
        "sort_new_messages",
        "confirm_scope",
        "mark_official",
        "mark_normal",
        "disconnect",
        "reconnect",
    ]

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .annotate(
                member_total=models.Count("members", distinct=True),
                message_total=models.Count("messages", distinct=True),
            )
        )

    @admin.display(description="Members", ordering="member_total")
    def member_count(self, source):
        return source.member_total

    @admin.display(description="Messages", ordering="message_total")
    def message_count(self, source):
        return source.message_total

    @admin.action(description="Confirm what these groups are for (their scope)")
    def confirm_scope(self, request, queryset):
        count = queryset.update(scope_confirmed=True, updated_at=timezone.now())
        self.message_user(request, f"Scope confirmed for {count} group(s).")

    @admin.action(description="Mark as official (university or staff channels)")
    def mark_official(self, request, queryset):
        count = queryset.update(trust=Source.Trust.OFFICIAL, updated_at=timezone.now())
        self.message_user(request, f"{count} group(s) marked official.")

    @admin.action(description="Mark as normal (not official)")
    def mark_normal(self, request, queryset):
        count = queryset.update(trust=Source.Trust.NORMAL, updated_at=timezone.now())
        self.message_user(request, f"{count} group(s) marked normal.")

    @admin.action(description="Disconnect (UniFlow stops reading these groups)")
    def disconnect(self, request, queryset):
        count = queryset.update(status=Source.Status.DISCONNECTED, updated_at=timezone.now())
        self.message_user(request, f"{count} group(s) disconnected; new messages are ignored.")

    @admin.action(description="Reconnect (read these groups again)")
    def reconnect(self, request, queryset):
        count = queryset.filter(status=Source.Status.DISCONNECTED).update(
            status=Source.Status.ACTIVE, updated_at=timezone.now()
        )
        self.message_user(request, f"{count} group(s) reconnected.")

    @admin.action(description="Sort new messages now (academic or noise)")
    def sort_new_messages(self, request, queryset):
        for source in queryset:
            triage_source.delay(source.id)
        self.message_user(request, f"Sorting started for {queryset.count()} group(s).")


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("sent_at", "source", "sender_name", "short_text", "triage")
    list_filter = ("triage", "source__platform", "source", "sent_at")
    search_fields = ("text", "sender_name")
    raw_id_fields = ("source", "reply_to")
    list_select_related = ("source",)
    actions = ["exclude_senders"]

    @admin.display(description="Text")
    def short_text(self, message):
        return message.text[:80]

    @admin.action(description="Stop reading these senders (they asked not to be read)")
    def exclude_senders(self, request, queryset):
        excluded = {
            services.exclude_sender(message, request.user, reason="Asked not to be read").pk
            for message in queryset.exclude(sender_ref="")
        }
        self.message_user(
            request, f"{len(excluded)} sender(s) excluded; their stored messages were erased."
        )


@admin.register(ExcludedSender)
class ExcludedSenderAdmin(admin.ModelAdmin):
    """People whose messages UniFlow skips. Add them with the action on Messages."""

    list_display = ("sender_name", "reason", "added_by", "created_at")
    search_fields = ("sender_name", "reason")
    readonly_fields = ("sender_ref", "sender_name", "added_by", "created_at")
    fields = ("sender_name", "sender_ref", "reason", "added_by", "created_at")

    def has_add_permission(self, request):
        return False


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


class InsightMentionInline(admin.TabularInline):
    model = InsightMention
    extra = 0
    fields = ("user", "matched_text")
    readonly_fields = ("user", "matched_text")
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


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
    list_filter = ("status", "origin", "kind", "publisher_type", "created_at")
    search_fields = ("title", "summary")
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
    inlines = [InsightEvidenceInline, InsightMentionInline]

    def get_inlines(self, request, obj):
        # A new staff post has no mentions yet: only show them on an existing insight.
        return self.inlines if obj else [InsightEvidenceInline]

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
            services.publish_insight(insight, request.user)
        self.message_user(request, f"Published {queryset.count()} item(s).")

    @admin.action(description="Retract selected (take them back)")
    def retract_selected(self, request, queryset):
        for insight in queryset:
            services.retract_insight(insight, request.user)
        self.message_user(request, f"Retracted {queryset.count()} item(s).")


@admin.register(TimetableImport)
class TimetableImportAdmin(admin.ModelAdmin):
    """Students' "Is this your timetable?" imports (read-only: students confirm them)."""

    list_display = ("created_at", "user", "status", "tab", "term", "confirmed_at")
    list_filter = ("status",)
    search_fields = ("user__email", "tab")
    readonly_fields = [field.name for field in TimetableImport._meta.fields]

    def has_add_permission(self, request):
        return False


@admin.register(Delivery)
class DeliveryAdmin(admin.ModelAdmin):
    """Who got which insight, at which level and why (read-only: worked out by code)."""

    list_display = ("insight", "user", "tier", "relevance", "reason", "read_at")
    list_filter = ("tier",)
    search_fields = ("user__email", "insight__title")
    list_select_related = ("insight", "user")
    readonly_fields = [field.name for field in Delivery._meta.fields]

    def has_add_permission(self, request):
        return False


@admin.register(DraftInsight)
class DraftInsightAdmin(admin.ModelAdmin):
    """The operator's queue: what the AI found but wasn't sure enough to publish (or held
    back, e.g. an unknown course), oldest first. Publish uses the same code as everywhere
    else (students get it in their feed and alerts); Reject takes it back for good."""

    list_display = ("title", "kind", "how_sure", "group", "quote", "created_at")
    list_filter = ("kind",)
    search_fields = ("title", "summary")
    ordering = ("created_at",)
    actions = ["publish_selected", "reject_selected"]
    list_display_links = ("title",)

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .filter(status=Status.DRAFT, origin=Insight.Origin.AI)
            .select_related("publisher_source")
            .prefetch_related("evidence")
        )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False  # open it under Insights to correct it

    @admin.display(description="How sure")
    def how_sure(self, insight):
        return f"{insight.confidence:.0%}"

    @admin.display(description="Group")
    def group(self, insight):
        return insight.publisher_source.title if insight.publisher_source else ""

    @admin.display(description="Quote")
    def quote(self, insight):
        first = next(iter(insight.evidence.all()), None)
        return first.quote[:120] if first else ""

    @admin.action(description="Publish (students get it, with alerts as usual)")
    def publish_selected(self, request, queryset):
        for insight in queryset:
            services.publish_insight(insight, request.user)
        self.message_user(request, f"Published {queryset.count()} item(s).")

    @admin.action(description="Reject (take it back; students never see it)")
    def reject_selected(self, request, queryset):
        count = 0
        for insight in queryset:
            services.retract_insight(insight, request.user)
            count += 1
        self.message_user(request, f"Rejected {count} item(s).")


@admin.register(AICall)
class AICallAdmin(admin.ModelAdmin):
    """Every AI request: filter by date ("Today") and model to see how much of each model's
    free daily allowance is used (kept 90 days)."""

    list_display = ("created_at", "kind", "model", "outcome", "detail")
    list_filter = ("created_at", "outcome", "kind", "model")
    readonly_fields = [field.name for field in AICall._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
