"""AIU's academic structure, used for student profiles and audience targeting.

Terminology (docs/03-data-model.md), matching https://aiu.edu.my/academic-programmes/:
- School: an academic school, e.g. School of Computing and Informatics. The Centre for
  Foundation and General Studies is also stored as a School.
- Programme: the student's degree / programme of study, e.g. Bachelor in Computer Science
  (Honours). Every programme belongs to one school.
- Intake: the batch a student joined with, e.g. September 2024.
- Course: a subject, e.g. CDE2313. Every course belongs to one school.
- Term: a semester, e.g. 2025/2026 Semester 1. AIU publishes two calendars (Undergraduate
  and Foundation, with different dates). The current term is worked out from the dates
  (Term.current), so nobody has to mark it by hand.
"""

import re
from datetime import date, timedelta

from django.db import models
from django.db.models import F, Max, Q

from core.models import TimeStampedModel


class School(TimeStampedModel):
    code = models.CharField(max_length=20, unique=True, help_text="Short code, e.g. SCI.")
    name = models.CharField(max_length=150)
    is_active = models.BooleanField(
        default=True, help_text="Inactive schools are hidden but kept for history."
    )

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Programme(TimeStampedModel):
    class Level(models.TextChoices):
        FOUNDATION = "foundation", "Foundation"
        DIPLOMA = "diploma", "Diploma"
        BACHELOR = "bachelor", "Bachelor"
        MASTER = "master", "Master"
        PHD = "phd", "PhD"

    # PROTECT: a school cannot be deleted while programmes still belong to it.
    school = models.ForeignKey(School, on_delete=models.PROTECT, related_name="programmes")
    code = models.CharField(max_length=20, unique=True, help_text="Short code, e.g. BCS.")
    name = models.CharField(max_length=200)
    level = models.CharField(max_length=20, choices=Level)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Intake(TimeStampedModel):
    code = models.CharField(max_length=20, unique=True, help_text="Short code, e.g. 2024-SEP.")
    name = models.CharField(max_length=100, help_text="Display name, e.g. September 2024.")
    start_date = models.DateField()
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-start_date"]  # newest intake first

    def __str__(self) -> str:
        return self.name


class Course(TimeStampedModel):
    # PROTECT: a school cannot be deleted while courses still belong to it.
    school = models.ForeignKey(School, on_delete=models.PROTECT, related_name="courses")
    code = models.CharField(max_length=20, unique=True, help_text="Course code, e.g. CDE2313.")
    name = models.CharField(max_length=200)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["code"]

    def __str__(self) -> str:
        return f"{self.code} {self.name}"


class Term(TimeStampedModel):
    class Calendar(models.TextChoices):
        UNDERGRADUATE = "undergraduate", "Undergraduate"
        FOUNDATION = "foundation", "Foundation"

    calendar = models.CharField(max_length=20, choices=Calendar, default=Calendar.UNDERGRADUATE)
    name = models.CharField(max_length=100, help_text="Display name, e.g. 2025/2026 Semester 1.")
    academic_session = models.CharField(max_length=20, help_text="e.g. 2025/26.")
    number = models.PositiveSmallIntegerField(help_text="Semester number within the session.")
    starts_on = models.DateField()
    ends_on = models.DateField()
    estimated = models.BooleanField(
        default=False,
        help_text="Dates worked out from last year's calendar (Term.estimate_after). Untick "
        "after checking them against the official calendar.",
    )

    class Meta:
        ordering = ["-starts_on"]  # newest term first
        constraints = [
            models.UniqueConstraint(
                fields=["calendar", "academic_session", "number"],
                name="academics_term_calendar_session_number",
            ),
            models.CheckConstraint(
                condition=Q(ends_on__gt=F("starts_on")), name="academics_term_ends_after_start"
            ),
        ]

    def __str__(self) -> str:
        return self.name

    @classmethod
    def current(cls, calendar: str, on: date) -> "Term | None":
        """The calendar's current term on date `on`:
        - during a term: that term;
        - during a break: the next term (so students can set up their new classes before it
          starts). If it isn't loaded yet, it is worked out from last year's calendar
          (estimate_after), so nobody has to add each semester by hand.
        """
        terms = cls.objects.filter(calendar=calendar)
        found = (
            terms.filter(starts_on__lte=on, ends_on__gte=on).first()
            or terms.filter(starts_on__gt=on).order_by("starts_on").first()
        )
        if found:
            return found
        term = terms.filter(ends_on__lt=on).order_by("-ends_on").first()
        for _ in range(6):  # at most two years of missing semesters
            following = cls.estimate_after(term) if term else None
            if following is None:
                break
            term = following
            if term.ends_on >= on:
                break
        return term

    @classmethod
    def next_after(cls, term: "Term") -> "Term | None":
        """The term after `term`: the next loaded one, or one worked out from last year."""
        return cls.objects.filter(calendar=term.calendar, starts_on__gt=term.starts_on).order_by(
            "starts_on"
        ).first() or cls.estimate_after(term)

    @staticmethod
    def _shift_session(session: str, years: int) -> str | None:
        """ "2025/2026" (or "2025/26") moved by `years` years; None if it isn't in that form."""
        found = re.fullmatch(r"(\d{4})/(\d{2}|\d{4})", session)
        if not found:
            return None
        first, second = int(found[1]) + years, int(found[2]) + years
        return f"{first}/{second % 100:02d}" if len(found[2]) == 2 else f"{first}/{second}"

    @classmethod
    def estimate_after(cls, term: "Term") -> "Term | None":
        """The term after `term`, saved with dates worked out from the same semester a year
        earlier plus 52 weeks (the same weekday), and marked `estimated`. Returns the loaded
        term if it exists; None if there is no year-earlier semester to work from."""
        per_session = cls.objects.filter(calendar=term.calendar).aggregate(Max("number"))
        if term.number < (per_session["number__max"] or term.number):
            session, number = term.academic_session, term.number + 1
        else:
            session, number = cls._shift_session(term.academic_session, 1), 1
        if session is None:
            return None
        terms = cls.objects.filter(calendar=term.calendar)
        if loaded := terms.filter(academic_session=session, number=number).first():
            return loaded
        year_before = terms.filter(
            academic_session=cls._shift_session(session, -1), number=number
        ).first()
        if year_before is None or year_before == term:  # one semester alone says too little
            return None
        prefix = "Foundation " if term.calendar == cls.Calendar.FOUNDATION else ""
        estimated, _ = cls.objects.get_or_create(
            calendar=term.calendar,
            academic_session=session,
            number=number,
            defaults={
                "name": f"{prefix}{session} Semester {number}",
                "starts_on": year_before.starts_on + timedelta(weeks=52),
                "ends_on": year_before.ends_on + timedelta(weeks=52),
                "estimated": True,
            },
        )
        return estimated
