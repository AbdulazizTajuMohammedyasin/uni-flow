from datetime import UTC, date, datetime, time

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from apps.academics.models import Course, School, Term
from apps.accounts import semesters
from apps.accounts.services import create_user
from apps.timetable.models import ClassMeeting, CourseSection, SectionEnrollment

pytestmark = pytest.mark.django_db

TODAY = "/api/v1/timetable/today/"
WEEK = "/api/v1/timetable/week/"


@pytest.fixture
def student():
    school = School.objects.create(code="SCI", name="Computing")
    now = Term.objects.create(
        name="2025/2026 Semester 2",
        academic_session="2025/2026",
        number=2,
        starts_on=date(2026, 3, 23),
        ends_on=date(2026, 7, 17),
        is_current=True,
    )
    past = Term.objects.create(
        name="2025/2026 Semester 1",
        academic_session="2025/2026",
        number=1,
        starts_on=date(2025, 10, 27),
        ends_on=date(2026, 2, 27),
    )
    cde = Course.objects.create(school=school, code="CDE2313", name="Data Structures")
    mgt = Course.objects.create(school=school, code="MGT1001", name="Management")

    def section(course, term, code="A", active=True, meetings=()):
        new = CourseSection.objects.create(course=course, term=term, code=code, is_active=active)
        for weekday, start, end, kind in meetings:
            ClassMeeting.objects.create(
                section=new,
                weekday=weekday,
                start_time=time(start),
                end_time=time(end),
                meeting_type=kind,
                room="B2",
            )
        return new

    user = create_user("ali@student.aiu.edu.my", "Str0ng-pass-99", full_name="Ali")
    for joined in [
        section(cde, now, meetings=[(0, 10, 12, "lecture"), (2, 14, 16, "lab")]),
        section(mgt, now, meetings=[(0, 8, 10, "lecture")]),
        section(cde, past, meetings=[(0, 16, 18, "lecture")]),  # last term
        section(mgt, now, code="Z", active=False, meetings=[(1, 9, 10, "lecture")]),  # closed
    ]:
        SectionEnrollment.objects.create(user=user, section=joined)
    section(cde, now, code="B", meetings=[(4, 9, 11, "lecture")])  # not joined

    api = APIClient()
    api.force_authenticate(user)
    return api


def classes(day):
    return [(c["course_code"], c["start_time"]) for c in day["classes"]]


def test_today_lists_my_classes_in_time_order(student, monkeypatch):
    monkeypatch.setattr(semesters, "today", lambda: date(2026, 3, 30))  # a Monday
    body = student.get(TODAY).json()

    assert body["term"]["name"] == "2025/2026 Semester 2"
    [today] = body["days"]
    assert today["date"] == "2026-03-30"
    assert classes(today) == [("MGT1001", "08:00"), ("CDE2313", "10:00")]
    assert today["classes"][1]["room"] == "B2"


def test_week_runs_monday_to_sunday(student):
    days = student.get(WEEK, {"date": "2026-04-01"}).json()["days"]  # a Wednesday

    assert [d["date"] for d in days] == [
        "2026-03-30",
        "2026-03-31",
        "2026-04-01",
        "2026-04-02",
        "2026-04-03",
        "2026-04-04",
        "2026-04-05",
    ]
    assert classes(days[0]) == [("MGT1001", "08:00"), ("CDE2313", "10:00")]
    assert classes(days[2]) == [("CDE2313", "14:00")]
    assert days[2]["classes"][0]["meeting_type"] == "lab"
    assert all(d["classes"] == [] for d in days[3:])


def test_no_classes_outside_the_term(student):
    after = student.get(WEEK, {"date": "2026-07-20"}).json()["days"]  # term ended 17 July
    before = student.get(WEEK, {"date": "2026-03-20"}).json()["days"]  # starts 23 March
    assert all(d["classes"] == [] for d in after + before)


def test_today_uses_kuala_lumpur_time_just_after_midnight(student, monkeypatch):
    # 16:30 UTC on Sunday 29 March is 00:30 on Monday 30 March in Kuala Lumpur (UTC+8).
    monkeypatch.setattr(timezone, "now", lambda: datetime(2026, 3, 29, 16, 30, tzinfo=UTC))
    [today] = student.get(TODAY).json()["days"]
    assert today["date"] == "2026-03-30"
    assert classes(today) == [("MGT1001", "08:00"), ("CDE2313", "10:00")]


def test_without_a_current_term_everything_is_empty(student):
    Term.objects.update(is_current=False)
    body = student.get(WEEK).json()
    assert body["term"] is None
    assert all(d["classes"] == [] for d in body["days"])


def test_bad_date_staff_and_visitors(student):
    assert student.get(WEEK, {"date": "1 April"}).status_code == 400

    lecturer = create_user("lee@aiu.edu.my", "Str0ng-pass-99", full_name="Lee", role="lecturer")
    staff = APIClient()
    staff.force_authenticate(lecturer)
    assert staff.get(TODAY).status_code == 403
    assert APIClient().get(WEEK).status_code == 401
