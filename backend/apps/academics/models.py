"""AIU's academic structure, used for student profiles and audience targeting.

Terminology (docs/03-data-model.md), matching https://aiu.edu.my/academic-programmes/:
- School: an academic school, e.g. School of Computing and Informatics. The Centre for
  Foundation and General Studies is also stored as a School.
- Programme: the student's degree / programme of study, e.g. Bachelor in Computer Science
  (Honours). Every programme belongs to one school.
- Intake: the batch a student joined with, e.g. September 2024.
- Course: a subject, e.g. CDE2313. Every course belongs to one school.
- Term: a semester, e.g. 2025/26 Semester 1. Exactly one term can be the current one.
"""

from django.db import models, transaction
from django.db.models import F, Q

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
    name = models.CharField(max_length=100, help_text="Display name, e.g. 2025/26 Semester 1.")
    academic_session = models.CharField(max_length=20, help_text="e.g. 2025/26.")
    number = models.PositiveSmallIntegerField(help_text="Semester number within the session.")
    starts_on = models.DateField()
    ends_on = models.DateField()
    is_current = models.BooleanField(default=False)

    class Meta:
        ordering = ["-starts_on"]  # newest term first
        constraints = [
            models.UniqueConstraint(
                fields=["academic_session", "number"], name="academics_term_session_number"
            ),
            models.CheckConstraint(
                condition=Q(ends_on__gt=F("starts_on")), name="academics_term_ends_after_start"
            ),
        ]

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        # Only one current term: marking this one current un-marks the others.
        with transaction.atomic():
            if self.is_current:
                Term.objects.filter(is_current=True).exclude(pk=self.pk).update(is_current=False)
            super().save(*args, **kwargs)
