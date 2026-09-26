"""Academics API addresses, mounted at /api/v1/academics/ (see config/api_v1.py)."""

from django.urls import path

from .views import IntakeListView, ProgrammeListView, SchoolListView

urlpatterns = [
    path("schools/", SchoolListView.as_view(), name="academics-schools"),
    path("programmes/", ProgrammeListView.as_view(), name="academics-programmes"),
    path("intakes/", IntakeListView.as_view(), name="academics-intakes"),
]
