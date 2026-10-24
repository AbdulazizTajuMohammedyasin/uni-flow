from datetime import date

import pytest
from django.db import IntegrityError, transaction
from django.utils import timezone
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


def make_term(
    number=1,
    starts=date(2025, 10, 27),
    ends=date(2026, 2, 27),
    session="2025/26",
    calendar="undergraduate",
):
    return Term.objects.create(
        calendar=calendar,
        name=f"{session} Semester {number}",
        academic_session=session,
        number=number,
        starts_on=starts,
        ends_on=ends,
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


@pytest.mark.parametrize(
    ("today", "expected"),
    [
        (date(2025, 11, 1), 1),  # during Semester 1
        (date(2026, 2, 27), 1),  # its last day
        (date(2026, 3, 1), 2),  # break: the next term is already loaded
        (date(2026, 8, 1), 1),  # break, nothing loaded after it: next one worked out (2026/27 S1)
        (date(2025, 1, 1), 1),  # before any term: the first one
    ],
)
def test_current_term_follows_the_dates(today, expected):
    make_term(number=1, starts=date(2025, 10, 27), ends=date(2026, 2, 27))
    make_term(number=2, starts=date(2026, 3, 23), ends=date(2026, 7, 17))

    assert Term.current("undergraduate", today).number == expected
    assert Term.current("foundation", today) is None  # no Foundation terms loaded


def test_a_missing_next_semester_is_worked_out_from_last_year():
    make_term(1, date(2025, 10, 27), date(2026, 2, 27), session="2025/2026")
    make_term(2, date(2026, 3, 23), date(2026, 7, 17), session="2025/2026")
    third = make_term(3, date(2026, 8, 3), date(2026, 10, 2), session="2025/2026")

    current = Term.current("undergraduate", date(2026, 10, 24))  # the break after Semester 3

    assert (current.name, current.academic_session, current.number) == (
        "2026/2027 Semester 1",
        "2026/2027",
        1,
    )
    # Last year's Semester 1 plus 52 weeks: the same weekdays (Monday to Friday).
    assert (current.starts_on, current.ends_on) == (date(2026, 10, 26), date(2027, 2, 26))
    assert current.estimated is True
    assert Term.next_after(third) == current  # worked out once, then reused
    assert Term.objects.filter(academic_session="2026/2027").count() == 1


def test_the_next_semester_in_the_same_session_and_the_foundation_name():
    make_term(1, date(2024, 10, 14), date(2025, 1, 24), "2024/25", "foundation")
    make_term(2, date(2025, 2, 10), date(2025, 5, 23), "2024/25", "foundation")
    first = make_term(1, date(2025, 10, 13), date(2026, 1, 23), "2025/26", "foundation")

    following = Term.next_after(first)

    assert (following.name, following.number) == ("Foundation 2025/26 Semester 2", 2)
    assert following.starts_on == date(2026, 2, 9)


def test_without_last_years_semester_nothing_is_guessed():
    only = make_term(1, date(2025, 10, 27), date(2026, 2, 27))
    assert Term.next_after(only) is None
    assert Term.current("undergraduate", date(2026, 3, 10)) == only  # the one that ended


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


def test_terms_list_and_current_term(client, monkeypatch):
    assert client.get(CURRENT_URL).status_code == 404

    monkeypatch.setattr(timezone, "localdate", lambda: date(2026, 4, 1))
    make_term(number=1)
    current = make_term(number=2, starts=date(2026, 3, 23), ends=date(2026, 7, 17))

    assert [t["number"] for t in client.get(TERMS_URL).json()] == [2, 1]  # newest first
    assert client.get(CURRENT_URL).json()["id"] == current.id


def test_login_required():
    assert APIClient().get(COURSES_URL).status_code == 401
    assert APIClient().get(CURRENT_URL).status_code == 401


def test_each_calendar_has_its_own_current_term(client, monkeypatch):
    monkeypatch.setattr(timezone, "localdate", lambda: date(2025, 11, 1))
    ug = make_term(number=1)
    foundation = make_term(
        number=1,  # same session and number is fine in another calendar
        starts=date(2025, 10, 13),
        ends=date(2026, 1, 23),
        calendar="foundation",
    )

    assert client.get(CURRENT_URL).json()["id"] == ug.id
    assert client.get(CURRENT_URL, {"calendar": "foundation"}).json()["id"] == foundation.id
    assert [t["id"] for t in client.get(TERMS_URL, {"calendar": "foundation"}).json()] == [
        foundation.id
    ]
    assert client.get(TERMS_URL, {"calendar": "masters"}).status_code == 400
