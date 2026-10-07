"""What the sources API accepts and returns."""

from rest_framework import serializers

from apps.academics.models import Course, Intake, Programme, School
from apps.timetable.models import CourseSection

from .models import Source


class SourceSerializer(serializers.ModelSerializer):
    """A group in "my groups"."""

    platform_label = serializers.CharField(source="get_platform_display", read_only=True)
    message_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Source
        fields = [
            "id",
            "title",
            "platform",
            "platform_label",
            "status",
            "school",
            "programme",
            "intake",
            "course",
            "section",
            "message_count",
        ]


class CreateSourceSerializer(serializers.Serializer):
    """POST sources/ — a group for pasted or uploaded messages, and what it is for."""

    title = serializers.CharField(max_length=200)
    school = serializers.PrimaryKeyRelatedField(
        queryset=School.objects.filter(is_active=True), required=False, allow_null=True
    )
    programme = serializers.PrimaryKeyRelatedField(
        queryset=Programme.objects.filter(is_active=True), required=False, allow_null=True
    )
    intake = serializers.PrimaryKeyRelatedField(
        queryset=Intake.objects.filter(is_active=True), required=False, allow_null=True
    )
    course = serializers.PrimaryKeyRelatedField(
        queryset=Course.objects.filter(is_active=True), required=False, allow_null=True
    )
    section = serializers.PrimaryKeyRelatedField(
        queryset=CourseSection.objects.filter(is_active=True), required=False, allow_null=True
    )


class PasteSerializer(serializers.Serializer):
    """POST sources/{id}/paste/ — text copied from WhatsApp, or one plain message."""

    text = serializers.CharField(max_length=100_000)
    sender_name = serializers.CharField(max_length=150, required=False, allow_blank=True)


class ExportSerializer(serializers.Serializer):
    """POST sources/{id}/export/ — WhatsApp's "Export chat" .txt file (multipart)."""

    file = serializers.FileField()


class ImportResultSerializer(serializers.Serializer):
    added = serializers.IntegerField(help_text="New messages stored.")
    already_stored = serializers.IntegerField(help_text="Messages UniFlow already had.")


# --- Timetable imports (/api/v1/timetable/imports/) -------------------------------------


class TimetableImportSerializer(serializers.Serializer):
    """A student's "Is this your timetable?"."""

    id = serializers.IntegerField()
    status = serializers.CharField(help_text="reading, ready, confirmed, discarded or failed")
    file_name = serializers.CharField()
    tab = serializers.CharField(help_text="The spreadsheet tab shown (blank for an image or PDF).")
    tabs = serializers.ListField(child=serializers.CharField(), help_text="Tabs with classes.")
    rows = serializers.JSONField(help_text="The classes read (course, section, meetings…).")
    report = serializers.JSONField(help_text="What confirming created or kept.")
    error = serializers.CharField()
    created_at = serializers.DateTimeField()


class StartImportSerializer(serializers.Serializer):
    """POST timetable/imports/ — a timetable file (multipart) or a Google Drive / Docs link."""

    file = serializers.FileField(required=False)
    link = serializers.URLField(required=False, max_length=1000)

    def validate(self, attrs):
        if bool(attrs.get("file")) == bool(attrs.get("link")):
            raise serializers.ValidationError("Send a file or a link (one of them).")
        return attrs


class UpdateImportSerializer(serializers.Serializer):
    """PATCH timetable/imports/{id}/ — another tab, or the classes to keep."""

    tab = serializers.CharField(required=False, allow_blank=True)
    rows = serializers.ListField(child=serializers.DictField(), required=False)


class ConfirmImportSerializer(serializers.Serializer):
    """POST timetable/imports/{id}/confirm/ — optionally the classes to keep."""

    rows = serializers.ListField(child=serializers.DictField(), required=False)


# --- The WhatsApp connector (/api/v1/internal/, connector.py) ---------------------------


class PendingSourceSerializer(serializers.ModelSerializer):
    """A group the connector should join."""

    class Meta:
        model = Source
        fields = ["id", "title", "invite_url"]


class JoinedSerializer(serializers.Serializer):
    """POST internal/sources/joined/ — the connector is in a group now."""

    external_id = serializers.CharField(max_length=100, help_text="WhatsApp's group id.")
    title = serializers.CharField(max_length=200, allow_blank=True, default="")
    source_id = serializers.IntegerField(required=False, allow_null=True)
    notice_sent = serializers.BooleanField(default=False)


class ConnectorMessageSerializer(serializers.Serializer):
    """POST internal/messages/ — one new group message."""

    source_external_id = serializers.CharField(max_length=100)
    message_id = serializers.CharField(max_length=100)
    sender_ref = serializers.CharField(max_length=200, allow_blank=True, default="")
    sender_name = serializers.CharField(max_length=150, allow_blank=True, default="")
    text = serializers.CharField(allow_blank=True, default="", trim_whitespace=False)
    sent_at = serializers.DateTimeField()
    reply_to = serializers.CharField(
        max_length=100, allow_blank=True, allow_null=True, default=None
    )
    has_files = serializers.BooleanField(default=False)


class ConnectorFileSerializer(serializers.Serializer):
    """POST internal/messages/{id}/files/ — a file attached to a group message."""

    file = serializers.FileField()
