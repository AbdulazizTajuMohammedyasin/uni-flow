"""Notifications API (/api/v1/notifications/): only the caller's own alerts, and the
student's phones that can get them as push notifications."""

from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import UserRole

from . import services
from .models import Notification, PushSettings
from .serializers import (
    DeviceSerializer,
    NotificationSerializer,
    PushSettingsSerializer,
    ReadAllSerializer,
    RegisteredSerializer,
    UnreadCountSerializer,
    UnregisterDeviceSerializer,
)


def my_notifications(request):
    return Notification.objects.filter(recipient=request.user)


@extend_schema(tags=["notifications"])
class NotificationListView(generics.ListAPIView):
    """GET notifications/ — my alerts, newest first (paginated)."""

    serializer_class = NotificationSerializer

    def get_queryset(self):
        return my_notifications(self.request)


@extend_schema(tags=["notifications"], responses=UnreadCountSerializer)
class UnreadCountView(APIView):
    """GET notifications/unread-count/ — for the bell badge (polled every 60 s)."""

    def get(self, request):
        count = my_notifications(request).filter(read_at__isnull=True).count()
        return Response({"count": count})


@extend_schema(tags=["notifications"], request=None, responses={204: None})
class ReadView(APIView):
    """POST notifications/{id}/read/ — 404 if it isn't mine."""

    def post(self, request, notification_id):
        notification = generics.get_object_or_404(my_notifications(request), pk=notification_id)
        if notification.read_at is None:
            notification.read_at = timezone.now()
            notification.save(update_fields=["read_at", "updated_at"])
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(tags=["notifications"], request=None, responses=ReadAllSerializer)
class ReadAllView(APIView):
    """POST notifications/read-all/"""

    def post(self, request):
        now = timezone.now()
        marked = (
            my_notifications(request)
            .filter(read_at__isnull=True)
            .update(read_at=now, updated_at=now)
        )
        return Response({"marked": marked})


# --- Phones (push notifications) ------------------------------------------------------------


def require_student(user) -> None:
    if user.role != UserRole.STUDENT:
        raise PermissionDenied("Only students get alerts on their phone.")


@extend_schema(tags=["notifications"], request=DeviceSerializer, responses=RegisteredSerializer)
class DeviceView(APIView):
    """POST notifications/devices/ — this phone can get my alerts (201 new, 200 again). The
    website inside the app calls it with the phone's push address on every page load."""

    throttle_scope = "devices"

    def post(self, request):
        require_student(request.user)
        serializer = DeviceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        created = services.register_device(request.user, **serializer.validated_data)
        return Response(
            {"registered": True}, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
        )


@extend_schema(tags=["notifications"], request=UnregisterDeviceSerializer, responses={204: None})
class UnregisterDeviceView(APIView):
    """POST notifications/devices/unregister/ — I'm logging out on this phone. Always 204, so
    nothing is revealed about addresses that aren't mine."""

    throttle_scope = "devices"

    def post(self, request):
        serializer = UnregisterDeviceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        services.unregister_device(request.user, serializer.validated_data["token"])
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(tags=["notifications"])
class PushSettingsView(generics.RetrieveUpdateAPIView):
    """GET / PATCH notifications/push-settings/ — which alerts reach my phone (all of them
    until I change it). The bell always shows everything."""

    serializer_class = PushSettingsSerializer
    http_method_names = ["get", "patch"]

    def get_object(self):
        require_student(self.request.user)
        if self.request.method == "GET":
            return PushSettings.objects.filter(user=self.request.user).first() or PushSettings(
                user=self.request.user
            )
        return PushSettings.objects.get_or_create(user=self.request.user)[0]
