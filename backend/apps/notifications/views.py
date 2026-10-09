"""Notifications API (/api/v1/notifications/): only the caller's own alerts."""

from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Notification
from .serializers import NotificationSerializer, ReadAllSerializer, UnreadCountSerializer


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
