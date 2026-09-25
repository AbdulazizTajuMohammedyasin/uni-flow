"""AIU's academic structure, used for student profiles and audience targeting.

Terminology (docs/03-data-model.md), matching https://aiu.edu.my/academic-programmes/:
- School: an academic school, e.g. School of Computing and Informatics. The Centre for
  Foundation and General Studies is also stored as a School.
- Programme: the student's degree / programme of study, e.g. Bachelor in Computer Science
  (Honours). Every programme belongs to one school.
- Intake: the batch a student joined with, e.g. September 2024.
Course and Term (for the timetable) are added in M7.
"""

from django.db import models

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
