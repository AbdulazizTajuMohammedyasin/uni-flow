"""Academics API addresses, mounted at /api/v1/academics/ (see config/api_v1.py)."""

from django.urls import path

from .views import (
    CourseListView,
    CurrentTermView,
    IntakeListView,
    ProgrammeListView,
    SchoolListView,
    TermListView,
)

urlpatterns = [
    path("schools/", SchoolListView.as_view(), name="academics-schools"),
    path("programmes/", ProgrammeListView.as_view(), name="academics-programmes"),
    path("intakes/", IntakeListView.as_view(), name="academics-intakes"),
    path("courses/", CourseListView.as_view(), name="academics-courses"),
    path("terms/", TermListView.as_view(), name="academics-terms"),
    path("terms/current/", CurrentTermView.as_view(), name="academics-current-term"),
]
