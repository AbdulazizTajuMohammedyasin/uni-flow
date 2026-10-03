from datetime import date, time

import pytest
from rest_framework.test import APIClient

from apps.academics.models import Course, Intake, Programme, School, Term
from apps.accounts import semesters
from apps.accounts.services import create_user
from apps.timetable.models import ClassMeeting, CourseSection, SectionEnrollment

pytestmark = pytest.mark.django_db

SECTIONS = "/api/v1/timetable/sections/"
MINE = "/api/v1/timetable/my-sections/"
PASSWORD = "Str0ng-pass-99"


@pytest.fixture
def world(monkeypatch):
    sci = School.objects.create(code="SCI", name="Computing")
    sbss = School.objects.create(code="SBSS", name="Business")
    bcs = Programme.objects.create(school=sci, code="BCS", name="CS", level="bachelor")
    fnd = Programme.objects.create(school=sci, code="FND", name="Foundation", level="foundation")
    intake = Intake.objects.create(code="2025-OCT", name="Oct 2025", start_date=date(2025, 10, 1))

    def term(calendar, number, starts, ends):
        return Term.objects.create(
            calendar=calendar,
            name=f"{calendar} {number}",
            academic_session="2025/2026",
            number=number,
            starts_on=starts,
            ends_on=ends,
        )

    # "Today" is 15 April 2026: inside `now` and `foundation_now`.
    monkeypatch.setattr(semesters, "today", lambda: date(2026, 4, 15))
    past = term("undergraduate", 1, date(2025, 10, 27), date(2026, 2, 27))
    now = term("undergraduate", 2, date(2026, 3, 23), date(2026, 7, 17))
    foundation_now = term("foundation", 2, date(2026, 2, 9), date(2026, 5, 22))

    cde = Course.objects.create(school=sci, code="CDE2313", name="Data Structures")
    mgt = Course.objects.create(school=sbss, code="MGT1001", name="Management")
    sections = {
        "cde_a": CourseSection.objects.create(course=cde, term=now, code="A"),
        "cde_b": CourseSection.objects.create(course=cde, term=now, code="B"),
        "mgt_a": CourseSection.objects.create(course=mgt, term=now, code="A"),
        "cde_old": CourseSection.objects.create(course=cde, term=past, code="A"),
        "cde_closed": CourseSection.objects.create(course=cde, term=now, code="Z", is_active=False),
        "fnd_a": CourseSection.objects.create(course=cde, term=foundation_now, code="F1"),
    }
    ClassMeeting.objects.create(
        section=sections["cde_a"], weekday=0, start_time=time(10), end_time=time(12), room="B2"
    )

    def student(email, programme):
        user = create_user(email, PASSWORD, full_name=email)
        profile = user.student_profile
        profile.school, profile.programme, profile.intake = sci, programme, intake
        profile.save()
        api = APIClient()
        api.force_authenticate(user)
        return user, api

    return {
        **sections,
        "sci": sci,
        "cde": cde,
        "now": now,
        "ali": student("ali@student.aiu.edu.my", bcs),
        "sara": student("sara@student.aiu.edu.my", bcs),
        "fnd": student("fnd@student.aiu.edu.my", fnd),
    }


def codes(response):
    return [f"{s['course']['code']}-{s['code']}" for s in response.json()["results"]]


# --- Browsing sections ---------------------------------------------------------------


def test_catalogue_shows_active_sections_of_my_current_term(world):
    _, api = world["ali"]

    assert codes(api.get(SECTIONS)) == ["CDE2313-A", "CDE2313-B", "MGT1001-A"]
    assert codes(api.get(SECTIONS, {"search": "manage"})) == ["MGT1001-A"]
    assert codes(api.get(SECTIONS, {"school": world["sci"].id})) == ["CDE2313-A", "CDE2313-B"]
    assert codes(api.get(SECTIONS, {"course": world["cde"].id})) == ["CDE2313-A", "CDE2313-B"]
    assert api.get(SECTIONS, {"school": "abc"}).status_code == 400

    first = api.get(SECTIONS).json()["results"][0]
    assert first["meetings"][0]["weekday_label"] == "Monday"
    assert first["meetings"][0]["room"] == "B2"


def test_foundation_students_see_the_foundation_term(world):
    _, api = world["fnd"]
    assert codes(api.get(SECTIONS)) == ["CDE2313-F1"]


def test_login_required():
    assert APIClient().get(SECTIONS).status_code == 401
    assert APIClient().get(MINE).status_code == 401


# --- My sections -----------------------------------------------------------------------


def test_join_list_and_leave_a_section(world):
    user, api = world["ali"]
    section = world["cde_a"]

    assert api.post(MINE, {"section": section.id}, format="json").status_code == 201
    assert api.post(MINE, {"section": section.id}, format="json").status_code == 201  # no-op
    assert SectionEnrollment.objects.filter(user=user).count() == 1
    assert [s["id"] for s in api.get(MINE).json()] == [section.id]

    assert api.delete(f"{MINE}{section.id}/").status_code == 204
    assert api.get(MINE).json() == []
    assert api.delete(f"{MINE}{section.id}/").status_code == 404


def test_only_active_sections_of_the_current_term_can_be_joined(world):
    _, api = world["ali"]
    for key in ("cde_old", "cde_closed", "fnd_a"):  # past term, inactive, other calendar
        response = api.post(MINE, {"section": world[key].id}, format="json")
        assert response.status_code == 400
        assert "section" in response.json()["error"]["fields"]


def test_staff_have_no_sections(world):
    lecturer = create_user("lee@aiu.edu.my", PASSWORD, full_name="Lee", role="lecturer")
    api = APIClient()
    api.force_authenticate(lecturer)
    assert api.get(MINE).status_code == 403
    assert api.post(MINE, {"section": world["cde_a"].id}, format="json").status_code == 403


# --- Adding a class by hand ---------------------------------------------------------


def new_class(**overrides):
    return {
        "course_code": "cde 3101",
        "course_name": "Operating Systems",
        "section": "a",
        "meetings": [
            {"weekday": 1, "start_time": "08:00", "end_time": "10:00", "room": "C1"},
            {"weekday": 3, "start_time": "14:00", "end_time": "16:00", "meeting_type": "lab"},
        ],
        **overrides,
    }


def test_add_a_missing_class_creates_it_once_and_joins(world):
    ali, ali_api = world["ali"]
    sara, sara_api = world["sara"]

    first = ali_api.post(SECTIONS, new_class(), format="json")
    assert first.status_code == 201
    body = first.json()
    assert body["course"]["code"] == "CDE3101"  # spaces removed, upper case
    assert body["code"] == "A"
    assert body["source"] == "student"
    assert len(body["meetings"]) == 2
    section = CourseSection.objects.get(pk=body["id"])
    assert section.created_by == ali
    assert section.course.school == world["sci"]  # the student's school
    assert section.term == world["now"]

    # A classmate adds the same class: it is reused, and its classes are not changed.
    second = sara_api.post(
        SECTIONS,
        new_class(meetings=[{"weekday": 4, "start_time": "09:00", "end_time": "11:00"}]),
        format="json",
    )
    assert second.status_code == 200
    assert second.json()["id"] == section.id
    assert section.meetings.count() == 2
    assert SectionEnrollment.objects.filter(section=section).count() == 2


def test_add_a_class_for_an_existing_course_uses_that_course(world):
    _, api = world["ali"]
    response = api.post(SECTIONS, new_class(course_code="CDE2313", section="C"), format="json")
    assert response.status_code == 201
    assert response.json()["course"]["id"] == world["cde"].id


def test_add_a_class_checks_its_input(world):
    _, api = world["ali"]
    bad_time = new_class(meetings=[{"weekday": 1, "start_time": "10:00", "end_time": "09:00"}])
    assert api.post(SECTIONS, bad_time, format="json").status_code == 400
    assert api.post(SECTIONS, new_class(meetings=[]), format="json").status_code == 400


def test_without_any_terms_nothing_can_be_added(world):
    _, api = world["ali"]
    CourseSection.objects.filter(term__calendar="undergraduate").delete()
    Term.objects.filter(calendar="undergraduate").delete()

    assert api.get(SECTIONS).json()["results"] == []
    assert api.post(SECTIONS, new_class(), format="json").status_code == 400
    assert api.post(MINE, {"section": world["cde_a"].id}, format="json").status_code == 400
