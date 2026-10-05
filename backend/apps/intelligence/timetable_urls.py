"""Addresses for "Add my timetable", mounted at /api/v1/timetable/imports/ (api_v1.py)."""

from django.urls import path

from .views import (
    ConfirmImportView,
    DiscardImportView,
    TimetableImportDetailView,
    TimetableImportListView,
)

urlpatterns = [
    path("", TimetableImportListView.as_view(), name="timetable-imports"),
    path("<int:import_id>/", TimetableImportDetailView.as_view(), name="timetable-import"),
    path("<int:import_id>/confirm/", ConfirmImportView.as_view(), name="timetable-import-confirm"),
    path("<int:import_id>/discard/", DiscardImportView.as_view(), name="timetable-import-discard"),
]
