from datetime import date, time

import pytest
from django.db import IntegrityError, transaction
from django.db.models import ProtectedError

from apps.academics.models import Course, School, Term
from apps.accounts.services import create_user
from apps.timetable.models import ClassMeeting, CourseSection, SectionEnrollment

pytestmark = pytest.mark.django_db


@pytest.fixture
def section():
    school = School.objects.create(code="SCI", name="Computing")
    course = Course.objects.create(school=school, code="CDE2313", name="Data Structures")
    term = Term.objects.create(
        name="2025/26 Semester 1",
        academic_session="2025/26",
        number=1,
        starts_on=date(2025, 10, 1),
        ends_on=date(2026, 2, 28),
        is_current=True,
    )
    return CourseSection.objects.create(course=course, term=term, code="A")


def test_section_code_is_unique_per_course_and_term(section):
    with transaction.atomic(), pytest.raises(IntegrityError):
        CourseSection.objects.create(course=section.course, term=section.term, code="A")
    CourseSection.objects.create(course=section.course, term=section.term, code="B")  # fine
    assert str(section) == "CDE2313 Section A (2025/26 Semester 1)"


def test_external_ref_is_unique_per_term_but_can_be_empty(section):
    CourseSection.objects.create(course=section.course, term=section.term, code="B")  # no ref
    CourseSection.objects.create(
        course=section.course, term=section.term, code="C", external_ref="X1"
    )
    with transaction.atomic(), pytest.raises(IntegrityError):
        CourseSection.objects.create(
            course=section.course, term=section.term, code="D", external_ref="X1"
        )


def test_meeting_must_end_after_it_starts_and_weekday_is_valid(section):
    meeting = ClassMeeting.objects.create(
        section=section, weekday=0, start_time=time(10), end_time=time(12), room="B2"
    )
    assert str(meeting) == "CDE2313 Section A (2025/26 Semester 1) Monday 10:00"

    with transaction.atomic(), pytest.raises(IntegrityError):
        ClassMeeting.objects.create(
            section=section, weekday=0, start_time=time(12), end_time=time(10)
        )
    with transaction.atomic(), pytest.raises(IntegrityError):
        ClassMeeting.objects.create(
            section=section, weekday=7, start_time=time(9), end_time=time(10)
        )


def test_a_student_is_enrolled_once(section):
    student = create_user("ali@student.aiu.edu.my", "Str0ng-pass-99", full_name="Ali")
    SectionEnrollment.objects.create(user=student, section=section)
    with transaction.atomic(), pytest.raises(IntegrityError):
        SectionEnrollment.objects.create(user=student, section=section)


def test_deleting_a_section_removes_its_meetings_but_courses_are_protected(section):
    ClassMeeting.objects.create(section=section, weekday=1, start_time=time(8), end_time=time(10))
    with pytest.raises(ProtectedError):
        section.course.delete()

    section.delete()
    assert ClassMeeting.objects.count() == 0
