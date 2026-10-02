"""A student's semester, worked out from their intake and the real term dates.

Rule: a student's semester = the number of terms that have started since their intake
(counting the first one), never less than 1. Terms come from the Term table, which holds
AIU's official calendars (three semesters a year; the dates change every year, e.g.
Semester 1 started 28 Oct 2024 and 27 Oct 2025). See `seed_academics` for the source.
Foundation students follow the Foundation calendar, everyone else the Undergraduate one.
Example: October 2025 intake -> Semester 1 from 27 Oct 2025, 2 from 23 Mar 2026,
3 from 3 Aug 2026.
A student can override it in their profile (deferral, repeated semester).
"""

from datetime import date, timedelta

from django.utils import timezone

from apps.academics.models import Programme, Term


def today() -> date:
    """Today in Kuala Lumpur (the project's TIME_ZONE)."""
    return timezone.localdate()


def calendar_for(programme: Programme | None) -> str:
    """Foundation programmes use the Foundation calendar; all others the Undergraduate one."""
    if programme is not None and programme.level == Programme.Level.FOUNDATION:
        return Term.Calendar.FOUNDATION
    return Term.Calendar.UNDERGRADUATE


def term_starts(on: date, calendar: str = Term.Calendar.UNDERGRADUATE) -> list[date]:
    """Start dates of the calendar's terms that started on or before `on`, newest first."""
    return list(
        Term.objects.filter(calendar=calendar, starts_on__lte=on)
        .order_by("-starts_on")
        .values_list("starts_on", flat=True)
    )


def semester_from_starts(intake_start: date, starts: list[date]) -> int:
    """Semester for an intake, given term starts (newest first). No database access."""
    return max(1, sum(1 for start in starts if start >= intake_start))


def semester_for(intake_start: date, on: date, calendar: str = Term.Calendar.UNDERGRADUATE) -> int:
    return semester_from_starts(intake_start, term_starts(on, calendar))


def range_from_starts(semester_min: int | None, semester_max: int | None, starts: list[date]):
    """The intake start dates whose students are in semesters min..max.

    `starts` are term starts, newest first. Returns (earliest, latest); either can be None
    for "no limit". Used to filter students in the database without working out each
    student's semester.
    """
    # Semester >= min (for min > 1)  <=>  the min-th newest term started on/after the intake.
    latest = None
    if semester_min and semester_min > 1:
        if len(starts) < semester_min:
            return date(9999, 12, 31), date(1000, 1, 1)  # nobody is that far yet: empty range
        latest = starts[semester_min - 1]
    # Semester <= max  <=>  the (max + 1)-th newest term started before the intake.
    earliest = None
    if semester_max and len(starts) > semester_max:
        earliest = starts[semester_max] + timedelta(days=1)
    return earliest, latest


def intake_start_range(
    semester_min: int | None,
    semester_max: int | None,
    on: date,
    calendar: str = Term.Calendar.UNDERGRADUATE,
):
    return range_from_starts(semester_min, semester_max, term_starts(on, calendar))
