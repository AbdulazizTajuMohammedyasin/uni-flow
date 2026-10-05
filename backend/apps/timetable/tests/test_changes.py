from datetime import UTC, date, datetime, time

import pytest
from rest_framework.test import APIClient

from apps.academics.models import Course, School, Term
from apps.accounts import semesters
from apps.accounts.models import UserRole
from apps.accounts.services import create_user
from apps.intelligence.models import Insight, Message, Source
from apps.intelligence.services import publish_insight, retract_insight, save_ai_insight
from apps.timetable.models import ClassChange, ClassMeeting, CourseSection, SectionEnrollment

pytestmark = pytest.mark.django_db

CHANGES = "/api/v1/timetable/changes/"
WEEK = "/api/v1/timetable/week/?date=2026-10-05"  # Mon 5 – Sun 11 Oct 2026
TUESDAY, THURSDAY = "2026-10-06", "2026-10-08"


@pytest.fixture(autouse=True)
def today(monkeypatch):
    monkeypatch.setattr(semesters, "today", lambda: date(2026, 10, 5))


@pytest.fixture
def sections():
    term = Term.objects.create(
        name="2026/2027 Semester 1",
        academic_session="2026/2027",
        number=1,
        starts_on=date(2026, 9, 28),
        ends_on=date(2027, 1, 29),
    )
    school = School.objects.create(code="SCI", name="Computing")
    course = Course.objects.create(school=school, code="CDE2313", name="Data Structures")
    found = {}
    for code in ("A", "B"):
        found[code] = CourseSection.objects.create(course=course, term=term, code=code)
        ClassMeeting.objects.create(
            section=found[code], weekday=1, start_time=time(10), end_time=time(12), room="B2"
        )
    return found


def student(email, section):
    user = create_user(email, "Str0ng-pass-99", full_name=email)
    SectionEnrollment.objects.create(user=user, section=section)
    api = APIClient()
    api.force_authenticate(user)
    return api


@pytest.fixture
def ali(sections):
    return student("ali@student.aiu.edu.my", sections["A"])


@pytest.fixture
def sara(sections):
    return student("sara@student.aiu.edu.my", sections["A"])


@pytest.fixture
def bob(sections):
    return student("bob@student.aiu.edu.my", sections["B"])


def found(sections, kind="class_moved", confidence=0.9, hold=False, **data) -> Insight:
    """What the AI found (M5.6) in a message of a group."""
    group = Source.objects.create(platform="manual", title="CDE2313 Sec A")
    message = Message.objects.create(
        source=group,
        external_id=f"m-{kind}",
        sender_name="Dr Lee",
        text="Tomorrow's class moves to 2 PM.",
        sent_at=datetime(2026, 10, 5, 1, 0, tzinfo=UTC),
    )
    return save_ai_insight(
        source=group,
        kind=kind,
        title="CDE2313 class moved",
        summary="Tomorrow's CDE2313 class moves to 2 PM.",
        confidence=confidence,
        evidence=[(message, message.text)],
        audience={"sections": [sections["A"]]},
        hold=hold,
        data={
            "section_ids": [sections["A"].id],
            "date": TUESDAY,
            "new_date": "",
            "old_start": "",
            "new_start": "",
            "new_end": "",
            "new_room": "",
        }
        | data,
    )


def tuesday(api) -> list[dict]:
    return api.get(WEEK).json()["days"][1]["classes"]


def day(api, index) -> list[dict]:
    return api.get(WEEK).json()["days"][index]["classes"]


def test_a_found_change_is_proposed_to_its_section_with_the_evidence(sections, ali, bob):
    insight = found(sections, new_start="14:00")

    [change] = ali.get(CHANGES).json()
    assert change["kind"] == "class_moved"
    assert change["course_code"] == "CDE2313"
    assert change["section_code"] == "A"
    assert change["date"] == TUESDAY
    assert (change["old_start"], change["old_end"]) == ("10:00", "12:00")
    assert (change["new_start"], change["new_end"]) == ("14:00", "16:00")  # same length
    assert change["my_status"] == "pending"
    assert change["evidence"][0]["quote"] == "Tomorrow's class moves to 2 PM."
    assert change["evidence"][0]["group"] == "CDE2313 Sec A"

    # Not answered yet: the class keeps its time and is only flagged.
    [lesson] = tuesday(ali)
    assert lesson["start_time"] == "10:00"
    assert lesson["change"] == {"id": change["id"], "kind": "class_moved", "status": "pending"}

    assert bob.get(CHANGES).json() == []  # Section B isn't affected
    assert tuesday(bob)[0]["change"] is None
    assert ClassChange.objects.get().insight == insight


def test_a_student_sees_only_their_own_confirmed_changes(sections, ali, sara):
    found(sections, new_start="14:00", new_room="C3")
    [change] = ali.get(CHANGES).json()

    response = ali.post(f"{CHANGES}{change['id']}/confirm/")
    assert response.status_code == 200
    assert response.json()["my_status"] == "confirmed"

    [lesson] = tuesday(ali)
    assert (lesson["start_time"], lesson["end_time"], lesson["room"]) == ("14:00", "16:00", "C3")
    assert lesson["change"]["status"] == "confirmed"

    [classmate] = tuesday(sara)  # Sara hasn't confirmed: her timetable is unchanged
    assert (classmate["start_time"], classmate["room"]) == ("10:00", "B2")
    assert sara.get(CHANGES).json()[0]["my_status"] == "pending"


def test_rejecting_changes_nothing_and_can_be_undone(sections, ali):
    found(sections, new_start="14:00")
    change_id = ali.get(CHANGES).json()[0]["id"]

    assert ali.post(f"{CHANGES}{change_id}/reject/").json()["my_status"] == "rejected"
    [lesson] = tuesday(ali)
    assert (lesson["start_time"], lesson["change"]) == ("10:00", None)

    ali.post(f"{CHANGES}{change_id}/confirm/")  # changed my mind
    assert tuesday(ali)[0]["start_time"] == "14:00"


def test_a_cancelled_class_stays_visible_and_flagged(sections, ali):
    found(sections, kind="class_cancelled")
    change_id = ali.get(CHANGES).json()[0]["id"]
    ali.post(f"{CHANGES}{change_id}/confirm/")

    [lesson] = tuesday(ali)
    assert lesson["change"] == {"id": change_id, "kind": "class_cancelled", "status": "confirmed"}


def test_a_class_moved_to_another_day(sections, ali):
    found(sections, new_date=THURSDAY, new_start="09:00", new_end="11:00")
    change = ali.get(CHANGES).json()[0]
    assert change["new_date"] == THURSDAY
    ali.post(f"{CHANGES}{change['id']}/confirm/")

    assert tuesday(ali) == []
    [moved] = day(ali, 3)
    assert (moved["course_code"], moved["start_time"], moved["room"]) == ("CDE2313", "09:00", "B2")


def test_an_extra_session_is_added_once_confirmed(sections, ali):
    found(sections, kind="extra_session", date="2026-10-10", new_start="10:00", new_end="12:00")
    change_id = ali.get(CHANGES).json()[0]["id"]
    assert day(ali, 5) == []  # Saturday: nothing until confirmed

    ali.post(f"{CHANGES}{change_id}/confirm/")
    [extra] = day(ali, 5)
    assert (extra["start_time"], extra["end_time"]) == ("10:00", "12:00")
    assert extra["change"]["kind"] == "extra_session"


def test_a_retracted_change_leaves_every_timetable(sections, ali):
    insight = found(sections, new_start="14:00")
    change_id = ali.get(CHANGES).json()[0]["id"]
    ali.post(f"{CHANGES}{change_id}/confirm/")

    retract_insight(insight, None)

    assert ali.get(CHANGES).json() == []
    assert tuesday(ali)[0]["start_time"] == "10:00"
    assert ali.post(f"{CHANGES}{change_id}/confirm/").status_code == 404

    publish_insight(insight, None)  # published again: the proposal comes back
    assert ali.get(CHANGES).json()[0]["my_status"] == "confirmed"


def test_a_draft_is_not_proposed_until_it_is_published(sections, ali):
    insight = found(sections, new_start="14:00", hold=True)
    assert ali.get(CHANGES).json() == []

    publish_insight(insight, None)  # an admin checked it
    assert len(ali.get(CHANGES).json()) == 1


def test_past_changes_are_not_listed(sections, ali):
    found(sections, date="2026-10-01")
    assert ali.get(CHANGES).json() == []


def test_only_students_have_changes(sections, ali):
    found(sections, new_start="14:00")
    staff = create_user("lee@aiu.edu.my", "Str0ng-pass-99", full_name="Lee", role=UserRole.LECTURER)
    api = APIClient()
    api.force_authenticate(staff)
    assert api.get(CHANGES).status_code == 403
    assert APIClient().get(CHANGES).status_code == 401
