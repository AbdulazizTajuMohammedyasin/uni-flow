"""Class timetable (docs/03-data-model.md, "timetable").

- CourseSection: one group of a course in one term, e.g. CDE2313 Section A, 2025/26 Sem 1.
- ClassMeeting: a weekly class of a section, e.g. Monday 10:00-12:00 in B2.
- SectionEnrollment: a student is in a section.
- ClassChange: a change to a section's class on one date, found by the AI in a message.
- ClassChangeConfirmation: a student confirmed or rejected a change.
Sections are shared: once one student (or the AI, or an admin) adds a section, everyone
picks the same one. Changes never edit ClassMeeting: each student's timetable shows the
changes they confirmed.
"""

from django.conf import settings
from django.db import models
from django.db.models import F, Q

from apps.academics.models import Course, Term
from core.models import TimeStampedModel


class CourseSection(TimeStampedModel):
    class Source(models.TextChoices):
        AI_IMPORT = "ai_import", "Read by AI from a timetable"
        STUDENT = "student", "Added by a student"
        ADMIN = "admin", "Added by an admin"
        FILE_IMPORT = "file_import", "Imported from a university file"

    course = models.ForeignKey(Course, on_delete=models.PROTECT, related_name="sections")
    term = models.ForeignKey(Term, on_delete=models.PROTECT, related_name="sections")
    code = models.CharField(max_length=20, help_text='Section code, e.g. "A" or "01".')
    lecturer_name = models.CharField(max_length=150, blank=True)
    is_active = models.BooleanField(default=True)
    source = models.CharField(max_length=20, choices=Source, default=Source.ADMIN)
    # NULL (not "") when missing, so sections without an id don't clash in the unique rule below.
    external_ref = models.CharField(  # noqa: DJ001
        max_length=64, null=True, blank=True, help_text="The university's own id, if any."
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )

    class Meta:
        ordering = ["course__code", "code"]
        constraints = [
            models.UniqueConstraint(
                fields=["course", "term", "code"], name="timetable_section_course_term_code"
            ),
            # MySQL allows many NULLs here, so only real university ids must be unique.
            models.UniqueConstraint(
                fields=["term", "external_ref"], name="timetable_section_term_external_ref"
            ),
        ]

    def __str__(self) -> str:
        return f"{self.course.code} Section {self.code} ({self.term.name})"


class ClassMeeting(TimeStampedModel):
    class Weekday(models.IntegerChoices):
        MONDAY = 0, "Monday"
        TUESDAY = 1, "Tuesday"
        WEDNESDAY = 2, "Wednesday"
        THURSDAY = 3, "Thursday"
        FRIDAY = 4, "Friday"
        SATURDAY = 5, "Saturday"
        SUNDAY = 6, "Sunday"

    class MeetingType(models.TextChoices):
        LECTURE = "lecture", "Lecture"
        TUTORIAL = "tutorial", "Tutorial"
        LAB = "lab", "Lab"
        OTHER = "other", "Other"

    section = models.ForeignKey(CourseSection, on_delete=models.CASCADE, related_name="meetings")
    weekday = models.PositiveSmallIntegerField(choices=Weekday)
    start_time = models.TimeField(help_text="Local time (Asia/Kuala_Lumpur).")
    end_time = models.TimeField()
    meeting_type = models.CharField(max_length=20, choices=MeetingType, default=MeetingType.LECTURE)
    building = models.CharField(max_length=100, blank=True)
    room = models.CharField(max_length=50, blank=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )

    class Meta:
        ordering = ["weekday", "start_time"]
        indexes = [models.Index(fields=["section", "weekday"])]
        constraints = [
            models.CheckConstraint(
                condition=Q(end_time__gt=F("start_time")), name="timetable_meeting_ends_after_start"
            ),
            models.CheckConstraint(
                condition=Q(weekday__gte=0, weekday__lte=6), name="timetable_meeting_weekday_range"
            ),
        ]

    def __str__(self) -> str:
        return f"{self.section} {self.get_weekday_display()} {self.start_time:%H:%M}"


class SectionEnrollment(TimeStampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="section_enrollments"
    )
    section = models.ForeignKey(CourseSection, on_delete=models.CASCADE, related_name="enrollments")

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "section"], name="timetable_enrollment_unique")
        ]

    def __str__(self) -> str:
        return f"{self.user} in {self.section}"


class ClassChangeKind(models.TextChoices):
    CLASS_MOVED = "class_moved", "Class moved"
    CLASS_CANCELLED = "class_cancelled", "Class cancelled"
    ROOM_CHANGED = "room_changed", "Room changed"
    EXTRA_SESSION = "extra_session", "Extra session"


class ClassChange(TimeStampedModel):
    """A proposed change to one section's class on one date, e.g. "CDE2313 Section A on
    Tue 6 Oct moves to 14:00". It comes from an AI insight (the message is its evidence);
    one insight can propose the same change for several sections."""

    Kind = ClassChangeKind  # ClassChange.Kind.CLASS_MOVED etc.

    class Status(models.TextChoices):
        PROPOSED = "proposed", "Proposed"
        RETRACTED = "retracted", "Taken back"

    insight = models.ForeignKey(
        "intelligence.Insight", on_delete=models.CASCADE, related_name="class_changes"
    )
    section = models.ForeignKey(CourseSection, on_delete=models.CASCADE, related_name="changes")
    meeting = models.ForeignKey(
        ClassMeeting,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        help_text="The weekly class it changes (empty for an extra session).",
    )
    kind = models.CharField(max_length=20, choices=Kind)
    date = models.DateField(help_text="The day of the class that changes.")
    new_date = models.DateField(null=True, blank=True, help_text="Moved to another day.")
    new_start = models.TimeField(null=True, blank=True)
    new_end = models.TimeField(null=True, blank=True)
    new_room = models.CharField(max_length=50, blank=True)
    status = models.CharField(max_length=20, choices=Status, default=Status.PROPOSED)

    class Meta:
        ordering = ["date", "id"]
        indexes = [models.Index(fields=["section", "date"])]
        constraints = [
            models.UniqueConstraint(
                fields=["insight", "section"], name="timetable_change_insight_section"
            )
        ]

    def __str__(self) -> str:
        return f"{self.get_kind_display()}: {self.section} on {self.date}"


class ClassChangeConfirmation(TimeStampedModel):
    """A student's answer to a proposed change. No row yet = they haven't decided."""

    class Status(models.TextChoices):
        CONFIRMED = "confirmed", "Confirmed"
        REJECTED = "rejected", "Rejected"

    change = models.ForeignKey(ClassChange, on_delete=models.CASCADE, related_name="confirmations")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="class_change_answers"
    )
    status = models.CharField(max_length=20, choices=Status)
    # Confirmed for every week from that date to the end of the term, not only that week
    # (only a moved class or a room change; see changes.REPEATABLE).
    every_week = models.BooleanField(default=False)
    decided_at = models.DateTimeField()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["change", "user"], name="timetable_confirmation_unique")
        ]

    def __str__(self) -> str:
        return f"{self.user} {self.status} {self.change}"
