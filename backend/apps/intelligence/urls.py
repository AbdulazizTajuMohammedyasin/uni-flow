"""Sources addresses, mounted at /api/v1/sources/ (see config/api_v1.py)."""

from django.urls import path

from .views import ExportView, PasteView, SourceListView

urlpatterns = [
    path("", SourceListView.as_view(), name="sources"),
    path("<int:source_id>/paste/", PasteView.as_view(), name="source-paste"),
    path("<int:source_id>/export/", ExportView.as_view(), name="source-export"),
]
