"""Sources addresses, mounted at /api/v1/sources/ (see config/api_v1.py)."""

from django.urls import path

from .views import (
    ClaimGroupView,
    ConnectSourceView,
    ExportView,
    LeaveSourceView,
    PasteView,
    SourceListView,
    UnclaimedGroupsView,
)

urlpatterns = [
    path("", SourceListView.as_view(), name="sources"),
    path("connect/", ConnectSourceView.as_view(), name="source-connect"),
    path("<int:source_id>/membership/", LeaveSourceView.as_view(), name="source-leave"),
    path("<int:source_id>/paste/", PasteView.as_view(), name="source-paste"),
    path("<int:source_id>/export/", ExportView.as_view(), name="source-export"),
    path("<int:source_id>/unclaimed/", UnclaimedGroupsView.as_view(), name="source-unclaimed"),
    path("<int:source_id>/claim/", ClaimGroupView.as_view(), name="source-claim"),
]
