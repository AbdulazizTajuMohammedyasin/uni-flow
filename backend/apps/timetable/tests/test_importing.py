from datetime import date, time

import pytest

from apps.academics.models import Course, School, Term
from apps.accounts.services import create_user
from apps.timetable.importing import (
    apply_timetable_rows,
    rows_from_json,
    rows_to_json,
    section_code,
)
from apps.timetable.models import ClassMeeting, CourseSection, SectionEnrollment

pytestmark = pytest.mark.django_db

CLASSES = [
    {
        "course_code": "cde 2313",
        "course_name": "Data Structures",
        "section": "a",
        "lecturer": "Dr Lee",
        "meetings": [
            {"day": "monday", "start": "10:00", "end": "12:00", "type": "lecture", "room": "B2"},
            {"day": "Wednesday", "start": "14:00", "end": "16:00", "type": "lab", "room": "Lab 3"},
        ],
    },
]


@pytest.fixture
def setting():
    school = School.objects.create(code="SCI", name="Computing")
    term = Term.objects.create(
        name="T1",
        academic_session="2025/2026",
        number=1,
        starts_on=date(2025, 10, 27),
        ends_on=date(2026, 2, 27),
    )
    student = create_user("ali@student.aiu.edu.my", "Str0ng-pass-99", full_name="Ali")
    return school, term, student


def test_rows_from_json_cleans_and_drops_what_is_invalid():
    rows = rows_from_json(
        [
            *CLASSES,
            {"course_code": "", "meetings": []},  # no course code
            {
                "course_code": "MGT1001",
                "meetings": [
                    {"day": "Funday", "start": "10:00", "end": "11:00"},
                    {"day": "tuesday", "start": "12:00", "end": "11:00"},  # ends first
                    {"day": "tuesday", "start": "9:5", "end": "nonsense"},
                    {"day": "friday", "start": "08:00", "end": "09:30", "type": "seminar"},
                ],
            },
        ]
    )
    assert [(r.course_code, r.section_code) for r in rows] == [("CDE2313", "A"), ("MGT1001", "1")]
    assert [(m.weekday, m.start_time, m.meeting_type) for m in rows[1].meetings] == [
        (4, time(8), "other")
    ]
    assert rows_to_json(rows_from_json(CLASSES))[0]["meetings"][1]["day"] == "wednesday"


@pytest.mark.parametrize(
    ("written", "code"),
    [
        ("A", "A"),
        ("grp a", "A"),
        ("Group A", "A"),
        ("Section 01", "01"),
        ("Sec. B", "B"),
        ("G1", "G1"),
    ],
)
def test_section_codes_are_written_one_way(written, code):
    assert section_code(written) == code


def test_missing_classes_are_created_and_the_student_enrolled(setting):
    school, term, student = setting
    report = apply_timetable_rows(
        term, rows_from_json(CLASSES), user=student, school=school, enroll=True
    )

    assert report.created_courses == ["CDE2313"]
    assert report.created_sections == ["CDE2313 Section A"]
    section = CourseSection.objects.get()
    assert (section.source, section.lecturer_name, section.created_by) == (
        "ai_import",
        "Dr Lee",
        student,
    )
    assert section.meetings.count() == 2
    assert SectionEnrollment.objects.filter(user=student, section=section).exists()


def test_existing_classes_are_never_changed(setting):
    school, term, student = setting
    course = Course.objects.create(school=school, code="CDE2313", name="Data Structures")
    section = CourseSection.objects.create(course=course, term=term, code="A")
    ClassMeeting.objects.create(section=section, weekday=0, start_time=time(9), end_time=time(11))

    report = apply_timetable_rows(term, rows_from_json(CLASSES), user=student, school=school)

    assert report.existing_sections == ["CDE2313 Section A"]
    assert len(report.differences) == 1
    assert list(section.meetings.values_list("start_time", flat=True)) == [time(9)]  # kept


def test_a_preview_saves_nothing(setting):
    school, term, student = setting
    report = apply_timetable_rows(
        term, rows_from_json(CLASSES), user=student, school=school, enroll=True, dry_run=True
    )
    assert report.created_sections == ["CDE2313 Section A"]
    assert Course.objects.count() == CourseSection.objects.count() == 0


def test_an_unknown_course_needs_a_school(setting):
    _, term, student = setting
    report = apply_timetable_rows(term, rows_from_json(CLASSES), user=student, school=None)
    assert report.errors and CourseSection.objects.count() == 0
