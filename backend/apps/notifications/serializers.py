"""What the notifications API returns."""

from rest_framework import serializers

from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    read = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = ["id", "kind", "title", "body", "target_type", "target_id", "read", "created_at"]

    def get_read(self, notification) -> bool:
        return notification.read_at is not None


class UnreadCountSerializer(serializers.Serializer):
    count = serializers.IntegerField()


class ReadAllSerializer(serializers.Serializer):
    marked = serializers.IntegerField(help_text="How many were unread.")
