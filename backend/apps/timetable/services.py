"""Timetable actions for students: which term is theirs, joining sections, adding a class,
and their classes for today or a week (with the class changes they confirmed).

Sections are shared: a section added by one student is the one everyone else picks.
Existing sections and their weekly classes are never changed by a student.
"""

from datetime import date, timedelta

from django.db import transaction
from rest_framework.exceptions import PermissionDenied, ValidationError

from apps.academics.models import Course, Term
from apps.accounts import semesters
from apps.accounts.models import UserRole

from .changes import apply_changes
from .models import ClassMeeting, CourseSection, SectionEnrollment


def require_student(user) -> None:
    if user.role != UserRole.STUDENT:
        raise PermissionDenied("Only students have their own sections.")


def _calendar_of(user) -> str:
    profile = getattr(user, "student_profile", None)
    return semesters.calendar_for(profile.programme if profile else None)


def current_term_for(user) -> Term | None:
    """The current term of the student's calendar (Foundation or Undergraduate)."""
    return Term.current(_calendar_of(user), semesters.today())


SEMESTERS = ("current", "next")


def semesters_for(user) -> tuple[Term | None, Term | None]:
    """The two terms a student can add classes to: this semester and the next one (its dates
    known or worked out from last year, see Term.next_after)."""
    current = current_term_for(user)
    return current, Term.next_after(current) if current else None


def term_for(user, semester: str = "current") -> Term:
    """The term the student chose ("current" or "next"), or a clear error."""
    current, following = semesters_for(user)
    term = following if semester == "next" else current
    if term is None:
        raise ValidationError("No terms have been added yet. Please try again later.")
    return term


def join_section(user, section: CourseSection) -> SectionEnrollment:
    """Add the student to a section of this or next semester (joining twice changes nothing)."""
    require_student(user)
    allowed = {term.id for term in semesters_for(user) if term}
    if section.term_id not in allowed or not section.is_active:
        raise ValidationError(
            {"section": "Only active sections of this or next semester can be added."}
        )
    enrollment, _ = SectionEnrollment.objects.get_or_create(user=user, section=section)
    return enrollment


@transaction.atomic
def add_section_by_hand(
    user,
    *,
    course_code: str,
    course_name: str,
    section_code: str,
    meetings: list[dict],
    semester: str = "current",
) -> tuple[CourseSection, bool]:
    """Find or create a course and its section in the current term, then join it.

    Returns (section, created). Weekly classes are only saved for a new section; an
    existing section keeps its classes (another student or the AI already added them).
    """
    require_student(user)
    term = term_for(user, semester)
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
                "meeting_id": meeting.id,
                "course_code": section.course.code,
                "course_name": section.course.name,
                "section_code": section.code,
                "lecturer_name": section.lecturer_name,
                "start_time": meeting.start_time,
                "end_time": meeting.end_time,
                "meeting_type": meeting.meeting_type,
                "building": meeting.building,
                "room": meeting.room,
                "change": None,
            }
        )
    return by_weekday


def classes_for_days(user, days: list[date]) -> dict:
    """The student's classes on each of `days`: the weekly classes of the term each day falls
    in (none between terms), so next semester's classes appear once it starts, plus the
    class changes they confirmed (see changes.py). `term` is the term of these days, or the
    current one if they are all between terms."""
    require_student(user)
    current = current_term_for(user)  # also works out a missing next term
    terms = list(
        Term.objects.filter(
            calendar=_calendar_of(user), starts_on__lte=max(days), ends_on__gte=min(days)
        ).order_by("starts_on")
    )
    slots: dict[int, dict[int, list[dict]]] = {}
    by_day = {}
    for day in days:
        term = next((t for t in terms if t.starts_on <= day <= t.ends_on), None)
        if term is None:
            by_day[day] = []
            continue
        if term.id not in slots:
            slots[term.id] = _class_slots(user, term)
        by_day[day] = [dict(slot) for slot in slots[term.id][day.weekday()]]
    apply_changes(user, by_day)
    term = terms[0] if terms else current
    return {
        "term": (
            {"id": term.id, "name": term.name, "starts_on": term.starts_on, "ends_on": term.ends_on}
            if term
            else None
        ),
        "days": [
            {"date": day, "weekday": day.weekday(), "classes": classes}
            for day, classes in by_day.items()
        ],
    }


def recent_terms_for(user) -> list[Term]:
    """Terms whose classes "My sections" shows: one that ended in the last 60 days (classes
    saved there can be moved on), this semester and the next."""
    current, following = semesters_for(user)
    ended = (
        Term.objects.filter(
            calendar=_calendar_of(user),
            ends_on__lt=semesters.today(),
            ends_on__gte=semesters.today() - timedelta(days=60),
        )
        .exclude(pk__in=[t.pk for t in (current, following) if t])
        .order_by("-ends_on")
        .first()
    )
    return [term for term in (ended, current, following) if term]


@transaction.atomic
def move_sections(user, from_term: Term) -> int:
    """Move my classes from a term that has ended to the current one (e.g. a timetable added
    before the new semester was known). The same course and section in the new term is used,
    or made from the old one with its weekly classes. Returns how many were moved."""
    require_student(user)
    target = term_for(user, "current")
    if from_term.ends_on >= semesters.today() or from_term == target:
        raise ValidationError(
            {"from_term": "Only classes of a semester that has ended can be moved."}
        )
    moved = 0
    for enrollment in SectionEnrollment.objects.filter(
        user=user, section__term=from_term
    ).select_related("section"):
        old = enrollment.section
        new, created = CourseSection.objects.get_or_create(
            course_id=old.course_id,
            term=target,
            code=old.code,
            defaults={
                "lecturer_name": old.lecturer_name,
                "source": old.source,
                "created_by": user,
                "updated_by": user,
            },
        )
        if created:
            ClassMeeting.objects.bulk_create(
                ClassMeeting(
                    section=new,
                    weekday=meeting.weekday,
                    start_time=meeting.start_time,
                    end_time=meeting.end_time,
                    meeting_type=meeting.meeting_type,
                    building=meeting.building,
                    room=meeting.room,
                    updated_by=user,
                )
                for meeting in old.meetings.all()
            )
        SectionEnrollment.objects.get_or_create(user=user, section=new)
        enrollment.delete()
        moved += 1
    return moved


def week_of(day: date) -> list[date]:
    """Monday to Sunday of the week that contains `day`."""
    monday = day - timedelta(days=day.weekday())
    return [monday + timedelta(days=offset) for offset in range(7)]
