"""Notifications addresses, mounted at /api/v1/notifications/ (see config/api_v1.py)."""

from django.urls import path

from .views import NotificationListView, ReadAllView, ReadView, UnreadCountView

urlpatterns = [
    path("", NotificationListView.as_view(), name="notifications"),
    path("unread-count/", UnreadCountView.as_view(), name="notifications-unread-count"),
    path("read-all/", ReadAllView.as_view(), name="notifications-read-all"),
    path("<int:notification_id>/read/", ReadView.as_view(), name="notification-read"),
]
