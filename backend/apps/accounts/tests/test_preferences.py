from datetime import date

import pytest
from django.core.management import call_command
from rest_framework.test import APIClient

from apps.academics.models import Intake
from apps.accounts import semesters
from apps.accounts.services import create_user

pytestmark = pytest.mark.django_db

ME = "/api/v1/auth/users/me/"
CHOICES = "/api/v1/auth/preferences/choices/"


@pytest.fixture
def student():
    return create_user("ali@student.aiu.edu.my", "Str0ng-pass-99", full_name="Ali")


@pytest.fixture
def client(student):
    api = APIClient()
    api.force_authenticate(student)
    return api


def test_choices_list_interests_and_info_types(client):
    body = client.get(CHOICES).json()
    assert {"value": "ai", "label": "Artificial Intelligence"} in body["interests"]
    assert {"value": "internship", "label": "Internships"} in body["info_types"]
    assert APIClient().get(CHOICES).status_code == 401


def test_student_saves_interests_info_types_and_nicknames(client):
    response = client.patch(
        ME,
        {
            "student_profile": {
                "interests": ["ai", "cybersecurity", "ai"],
                "info_types": ["internship"],
                "aliases": "Abdu, Aziz",
            }
        },
        format="json",
    )

    assert response.status_code == 200
    profile = response.json()["student_profile"]
    assert profile["interests"] == ["ai", "cybersecurity"]  # repeat removed
    assert profile["info_types"] == ["internship"]
    assert profile["aliases"] == "Abdu, Aziz"


def test_unknown_choices_are_refused(client):
    response = client.patch(ME, {"student_profile": {"interests": ["cooking"]}}, format="json")
    assert response.status_code == 400


def test_semester_is_worked_out_from_the_intake_unless_overridden(client, student, monkeypatch):
    monkeypatch.setattr(semesters, "today", lambda: date(2025, 10, 15))
    call_command("seed_academics", stdout=None)  # official terms
    intake = Intake.objects.get(code="2024-OCT")
    client.patch(ME, {"student_profile": {"intake": intake.id}}, format="json")

    assert (
        client.get(ME).json()["student_profile"]["current_semester"] == 3
    )  # Oct 24, Mar 25, Aug 25 terms

    client.patch(ME, {"student_profile": {"semester_override": 2}}, format="json")
    assert client.get(ME).json()["student_profile"]["current_semester"] == 2

    too_high = client.patch(ME, {"student_profile": {"semester_override": 20}}, format="json")
    assert too_high.status_code == 400
