"""The WhatsApp connector's private addresses, mounted at /api/v1/internal/ (see
connector.py). In production nginx doesn't let the internet reach them at all."""

from django.urls import path

from .views import ConnectorFileView, ConnectorMessageView, JoinedView, PendingSourcesView

urlpatterns = [
    path("sources/pending/", PendingSourcesView.as_view(), name="internal-pending-sources"),
    path("sources/joined/", JoinedView.as_view(), name="internal-joined"),
    path("messages/", ConnectorMessageView.as_view(), name="internal-messages"),
    path(
        "messages/<int:message_id>/files/",
        ConnectorFileView.as_view(),
        name="internal-message-files",
    ),
]
