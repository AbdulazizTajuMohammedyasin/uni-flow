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
