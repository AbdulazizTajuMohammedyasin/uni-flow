"""What the notifications API returns."""

from rest_framework import serializers

from .models import Device, Notification, PushSettings


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


EXPO_TOKEN = r"^Expo(nent)?PushToken\[[A-Za-z0-9_-]{1,200}\]$"


class DeviceSerializer(serializers.Serializer):
    """POST notifications/devices/: the phone's push address, from the app."""

    token = serializers.RegexField(
        EXPO_TOKEN, max_length=200, error_messages={"invalid": "This isn't a push address."}
    )
    platform = serializers.ChoiceField(choices=Device.Platform.choices)
    app_version = serializers.CharField(max_length=20, required=False, allow_blank=True)


class UnregisterDeviceSerializer(serializers.Serializer):
    token = serializers.CharField(max_length=200)


class RegisteredSerializer(serializers.Serializer):
    registered = serializers.BooleanField()


class PushSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = PushSettings
        fields = ["class_changes", "needs_you", "daily_digest"]
