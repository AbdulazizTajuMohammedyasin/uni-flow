"""Class timetable (docs/03-data-model.md, "timetable").

- CourseSection: one group of a course in one term, e.g. CDE2313 Section A, 2025/26 Sem 1.
- ClassMeeting: a weekly class of a section, e.g. Monday 10:00-12:00 in B2.
- SectionEnrollment: a student is in a section.
Sections are shared: once one student (or the AI, or an admin) adds a section, everyone
picks the same one. Changes detected in messages are stored separately (later, M5).
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
