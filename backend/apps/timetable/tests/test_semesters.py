"""This semester or the next: where a student's classes go, and when they show."""

from datetime import date, time

import pytest

from apps.academics.models import Term
from apps.accounts import semesters
from apps.timetable.models import ClassMeeting, CourseSection, SectionEnrollment
from apps.timetable.tests.test_api import MINE, SECTIONS, new_class
from apps.timetable.tests.test_api import world as world  # noqa: F401  (the shared fixture)

pytestmark = pytest.mark.django_db

SEMESTERS = "/api/v1/timetable/semesters/"
WEEK = "/api/v1/timetable/week/"
MOVE = "/api/v1/timetable/my-sections/move/"


def test_this_semester_and_the_next_one_worked_out_from_last_year(world):
    _, api = world["ali"]

    body = api.get(SEMESTERS).json()

    assert body["current"]["name"] == "undergraduate 2"
    assert body["next"]["name"] == "2026/2027 Semester 1"
    assert (body["next"]["starts_on"], body["next"]["estimated"]) == ("2026-10-26", True)


def test_a_class_added_for_next_semester_shows_only_once_it_starts(world):
    _, api = world["ali"]

    added = api.post(SECTIONS, new_class() | {"semester": "next"}, format="json")
    assert added.status_code == 201
    upcoming = Term.objects.get(academic_session="2026/2027")
    assert added.json()["semester"]["id"] == upcoming.id

    class_day = new_class()["meetings"][0]["weekday"]
    this_week = api.get(WEEK, {"date": "2026-04-13"}).json()["days"]
    first_week = api.get(WEEK, {"date": "2026-10-26"}).json()

    assert all(day["classes"] == [] for day in this_week)
    assert first_week["term"]["name"] == "2026/2027 Semester 1"
    assert [c["course_code"] for c in first_week["days"][class_day]["classes"]] == ["CDE3101"]


def test_my_sections_shows_both_semesters_each_named(world):
    user, api = world["ali"]
    api.post(MINE, {"section": world["cde_a"].id}, format="json")
    api.post(SECTIONS, new_class() | {"semester": "next"}, format="json")

    mine = api.get(MINE).json()

    assert [(s["course"]["code"], s["semester"]["name"]) for s in mine] == [
        ("CDE2313", "undergraduate 2"),
        ("CDE3101", "2026/2027 Semester 1"),
    ]


def test_a_section_of_next_semester_can_be_joined_but_not_an_old_one(world):
    _, api = world["ali"]
    upcoming = Term.next_after(world["now"])
    next_section = CourseSection.objects.create(course=world["cde"], term=upcoming, code="A")

    assert api.post(MINE, {"section": next_section.id}, format="json").status_code == 201
    assert api.post(MINE, {"section": world["cde_old"].id}, format="json").status_code == 400
    assert [s["id"] for s in api.get(SECTIONS, {"semester": "next"}).json()["results"]] == [
        next_section.id
    ]


def test_classes_saved_in_a_semester_that_ended_can_be_moved_on(world, monkeypatch):
    user, api = world["ali"]
    SectionEnrollment.objects.create(user=user, section=world["cde_a"])
    # Later: Semester 2 has ended, and the next one hadn't been loaded when Ali added classes.
    monkeypatch.setattr(semesters, "today", lambda: date(2026, 7, 25))
    mine = api.get(MINE).json()
    assert [s["semester"]["name"] for s in mine] == ["undergraduate 2"]  # still listed

    response = api.post(MOVE, {"from_term": world["now"].id}, format="json")

    assert response.json() == {"moved": 1}
    moved = SectionEnrollment.objects.get(user=user).section
    assert (moved.course.code, moved.code, moved.term.name) == (
        "CDE2313",
        "A",
        "2026/2027 Semester 1",
    )
    assert list(moved.meetings.values_list("weekday", "start_time")) == [(0, time(10))]
    assert ClassMeeting.objects.filter(section=world["cde_a"]).exists()  # the old one is kept


def test_classes_of_the_current_semester_cannot_be_moved(world):
    user, api = world["ali"]
    SectionEnrollment.objects.create(user=user, section=world["cde_a"])

    assert api.post(MOVE, {"from_term": world["now"].id}, format="json").status_code == 400
