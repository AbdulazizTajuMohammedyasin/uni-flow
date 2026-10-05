"""Student timetable addresses, mounted at /api/v1/timetable/ (see config/api_v1.py)."""

from django.urls import path

from .views import (
    ClassChangeDecisionView,
    ClassChangeListView,
    MySectionDeleteView,
    MySectionsView,
    SectionListView,
    TodayView,
    WeekView,
)

urlpatterns = [
    path("sections/", SectionListView.as_view(), name="timetable-sections"),
    path("my-sections/", MySectionsView.as_view(), name="timetable-my-sections"),
    path(
        "my-sections/<int:section_id>/",
        MySectionDeleteView.as_view(),
        name="timetable-my-section",
    ),
    path("today/", TodayView.as_view(), name="timetable-today"),
    path("week/", WeekView.as_view(), name="timetable-week"),
    path("changes/", ClassChangeListView.as_view(), name="timetable-changes"),
    path(
        "changes/<int:change_id>/confirm/",
        ClassChangeDecisionView.as_view(confirm=True),
        name="timetable-change-confirm",
    ),
    path(
        "changes/<int:change_id>/reject/",
        ClassChangeDecisionView.as_view(confirm=False),
        name="timetable-change-reject",
    ),
]
