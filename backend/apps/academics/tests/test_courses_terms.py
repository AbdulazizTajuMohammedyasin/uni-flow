from datetime import date

import pytest
from django.db import IntegrityError, transaction
from rest_framework.test import APIClient

from apps.academics.models import Course, School, Term
from apps.accounts.services import create_user

pytestmark = pytest.mark.django_db

COURSES_URL = "/api/v1/academics/courses/"
TERMS_URL = "/api/v1/academics/terms/"
CURRENT_URL = "/api/v1/academics/terms/current/"


@pytest.fixture
def client():
    api = APIClient()
    api.force_authenticate(create_user("ali@student.aiu.edu.my", "Str0ng-pass-99", full_name="Ali"))
    return api


def make_term(session="2025/26", number=1, current=False, starts=date(2025, 10, 1)):
    return Term.objects.create(
        name=f"{session} Semester {number}",
        academic_session=session,
        number=number,
        starts_on=starts,
        ends_on=date(starts.year + 1, 2, 28),
        is_current=current,
    )


# --- Models ---------------------------------------------------------------------------


def test_course_codes_are_unique():
    school = School.objects.create(code="SCI", name="Computing")
    Course.objects.create(school=school, code="CDE2313", name="Data Structures")
    with transaction.atomic(), pytest.raises(IntegrityError):
        Course.objects.create(school=school, code="CDE2313", name="Copy")


def test_term_must_end_after_it_starts_and_be_unique_per_session():
    make_term()
    with transaction.atomic(), pytest.raises(IntegrityError):
        make_term()  # same session and number
    with transaction.atomic(), pytest.raises(IntegrityError):
        Term.objects.create(
            name="Bad",
            academic_session="2026/27",
            number=1,
            starts_on=date(2026, 10, 1),
            ends_on=date(2026, 10, 1),
        )


def test_only_one_term_is_current():
    first = make_term(number=1, current=True)
    second = make_term(number=2, current=True, starts=date(2026, 3, 1))

    first.refresh_from_db()
    assert first.is_current is False
    assert second.is_current is True
    assert Term.objects.filter(is_current=True).count() == 1


# --- Read API ---------------------------------------------------------------------------


def test_courses_list_active_only_with_school_filter_and_search(client):
    sci = School.objects.create(code="SCI", name="Computing")
    sbss = School.objects.create(code="SBSS", name="Business")
    closed = School.objects.create(code="OLD", name="Closed school", is_active=False)
    Course.objects.create(school=sci, code="CDE2313", name="Data Structures")
    Course.objects.create(school=sci, code="CDE1001", name="Old course", is_active=False)
    Course.objects.create(school=sbss, code="BBA1001", name="Principles of Management")
    Course.objects.create(school=closed, code="OLD1001", name="Hidden")

    codes = [c["code"] for c in client.get(COURSES_URL).json()]
    assert codes == ["BBA1001", "CDE2313"]
    assert [c["code"] for c in client.get(COURSES_URL, {"school": sci.id}).json()] == ["CDE2313"]
    assert [c["code"] for c in client.get(COURSES_URL, {"search": "data"}).json()] == ["CDE2313"]
    assert client.get(COURSES_URL, {"school": "abc"}).status_code == 400


def test_terms_list_and_current_term(client):
    assert client.get(CURRENT_URL).status_code == 404

    make_term(number=1, starts=date(2025, 10, 1))
    current = make_term(number=2, current=True, starts=date(2026, 3, 1))

    assert [t["number"] for t in client.get(TERMS_URL).json()] == [2, 1]  # newest first
    assert client.get(CURRENT_URL).json()["id"] == current.id


def test_login_required():
    assert APIClient().get(COURSES_URL).status_code == 401
    assert APIClient().get(CURRENT_URL).status_code == 401


def test_each_calendar_has_its_own_current_term(client):
    ug = make_term(number=1, current=True)
    foundation = Term.objects.create(
        calendar="foundation",
        name="Foundation 2025/26 Semester 1",
        academic_session="2025/26",
        number=1,  # same session and number is fine in another calendar
        starts_on=date(2025, 10, 13),
        ends_on=date(2026, 1, 23),
        is_current=True,
    )

    ug.refresh_from_db()
    assert ug.is_current is True  # not un-marked by the Foundation term
    assert client.get(CURRENT_URL).json()["id"] == ug.id
    assert client.get(CURRENT_URL, {"calendar": "foundation"}).json()["id"] == foundation.id
    assert [t["id"] for t in client.get(TERMS_URL, {"calendar": "foundation"}).json()] == [
        foundation.id
    ]
    assert client.get(TERMS_URL, {"calendar": "masters"}).status_code == 400
