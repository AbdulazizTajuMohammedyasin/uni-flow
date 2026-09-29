"""Who a post is for (docs/03-data-model.md#audiences-mvp).

Each announcement, event or application listing owns one Audience row.
- Every field empty: all students.
- Inside one field: OR ("Computing or Business").
- Between fields: AND ("Computing and the October 2024 intake").
Checking which students match is in selectors.py (M2.5).
"""

from django.db import models

from apps.academics.models import Intake, Programme, School
from core.models import TimeStampedModel


class Audience(TimeStampedModel):
    schools = models.ManyToManyField(School, blank=True, related_name="+")
    programmes = models.ManyToManyField(Programme, blank=True, related_name="+")
    intakes = models.ManyToManyField(Intake, blank=True, related_name="+")

    def __str__(self) -> str:
        return self.summary()

    def summary(self) -> str:
        """Short text for lists, e.g. "School of Computing · Intake October 2024"."""
        schools = [school.name for school in self.schools.all()]
        programmes = [programme.name for programme in self.programmes.all()]
        intakes = [intake.name for intake in self.intakes.all()]
        parts = []
        if schools:
            parts.append(" or ".join(schools))
        if programmes:
            parts.append(" or ".join(programmes))
        if intakes:
            parts.append(("Intake " if len(intakes) == 1 else "Intakes ") + " or ".join(intakes))
        return " · ".join(parts) or "All students"
