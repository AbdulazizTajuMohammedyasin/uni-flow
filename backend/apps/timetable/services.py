"""Timetable actions for students: which term is theirs, joining sections, adding a class,
and their classes for today or a week.

Sections are shared: a section added by one student is the one everyone else picks.
Existing sections and their weekly classes are never changed by a student.
"""

from datetime import date, timedelta

from django.db import transaction
from rest_framework.exceptions import PermissionDenied, ValidationError

from apps.academics.models import Course, Term
from apps.accounts import semesters
from apps.accounts.models import UserRole

from .models import ClassMeeting, CourseSection, SectionEnrollment


def require_student(user) -> None:
    if user.role != UserRole.STUDENT:
        raise PermissionDenied("Only students have their own sections.")


def current_term_for(user) -> Term | None:
    """The current term of the student's calendar (Foundation or Undergraduate)."""
    profile = getattr(user, "student_profile", None)
    calendar = semesters.calendar_for(profile.programme if profile else None)
    return Term.current(calendar, semesters.today())


def _require_current_term(user) -> Term:
    term = current_term_for(user)
    if term is None:
        raise ValidationError("No terms have been added yet. Please try again later.")
    return term


def join_section(user, section: CourseSection) -> SectionEnrollment:
    """Add the student to a section of their current term (joining twice changes nothing)."""
    require_student(user)
    term = _require_current_term(user)
    if section.term_id != term.id or not section.is_active:
        raise ValidationError({"section": "Only active sections of the current term can be added."})
    enrollment, _ = SectionEnrollment.objects.get_or_create(user=user, section=section)
    return enrollment


@transaction.atomic
def add_section_by_hand(
    user, *, course_code: str, course_name: str, section_code: str, meetings: list[dict]
) -> tuple[CourseSection, bool]:
    """Find or create a course and its section in the current term, then join it.

    Returns (section, created). Weekly classes are only saved for a new section; an
    existing section keeps its classes (another student or the AI already added them).
    """
    require_student(user)
    term = _require_current_term(user)
    code = course_code.strip().upper().replace(" ", "")

    course = Course.objects.filter(code=code).first()
    if course is None:
        school = user.student_profile.school
        if school is None:
            raise ValidationError("Choose your school in your profile first.")
        course = Course.objects.create(school=school, code=code, name=course_name.strip())

    section, created = CourseSection.objects.get_or_create(
        course=course,
        term=term,
        code=section_code.strip().upper(),
        defaults={"source": CourseSection.Source.STUDENT, "created_by": user, "updated_by": user},
    )
    if created:
        ClassMeeting.objects.bulk_create(
            ClassMeeting(section=section, updated_by=user, **meeting) for meeting in meetings
        )
    SectionEnrollment.objects.get_or_create(user=user, section=section)
    return section, created


def _class_slots(user, term: Term) -> dict[int, list[dict]]:
    """The student's weekly classes this term, grouped by weekday (0 = Monday)."""
    meetings = (
        ClassMeeting.objects.filter(
            section__term=term, section__is_active=True, section__enrollments__user=user
        )
        .select_related("section__course")
        .order_by("start_time")
    )
    by_weekday: dict[int, list[dict]] = {day: [] for day in range(7)}
    for meeting in meetings:
        section = meeting.section
        by_weekday[meeting.weekday].append(
            {
                "section_id": section.id,
                "course_code": section.course.code,
                "course_name": section.course.name,
                "section_code": section.code,
                "lecturer_name": section.lecturer_name,
                "start_time": meeting.start_time,
                "end_time": meeting.end_time,
                "meeting_type": meeting.meeting_type,
                "building": meeting.building,
                "room": meeting.room,
            }
        )
    return by_weekday


def classes_for_days(user, days: list[date]) -> dict:
    """The student's classes on each of `days` (empty outside the current term)."""
    require_student(user)
    term = current_term_for(user)
    slots = _class_slots(user, term) if term else {}
    return {
        "term": {"id": term.id, "name": term.name} if term else None,
        "days": [
            {
                "date": day,
                "weekday": day.weekday(),
                "classes": slots[day.weekday()]
                if term and term.starts_on <= day <= term.ends_on
                else [],
            }
            for day in days
        ],
    }


def week_of(day: date) -> list[date]:
    """Monday to Sunday of the week that contains `day`."""
    monday = day - timedelta(days=day.weekday())
    return [monday + timedelta(days=offset) for offset in range(7)]
