"""Who a post is for (docs/03-data-model.md#audiences-mvp).

Each insight or post owns one Audience row.
- Every field empty: all students.
- Inside one field: OR ("Computing or Business").
- Between fields: AND ("Computing and the October 2024 intake").
- Courses match students in a section of that course in the *current* term;
  sections match the students in that exact section.
Checking which students match is in selectors.py.
"""

from django.db import models

from apps.academics.models import Course, Intake, Programme, School
from apps.timetable.models import CourseSection
from core.models import TimeStampedModel


class Audience(TimeStampedModel):
    schools = models.ManyToManyField(School, blank=True, related_name="+")
    programmes = models.ManyToManyField(Programme, blank=True, related_name="+")
    intakes = models.ManyToManyField(Intake, blank=True, related_name="+")
    courses = models.ManyToManyField(Course, blank=True, related_name="+")
    sections = models.ManyToManyField(CourseSection, blank=True, related_name="+")

    def __str__(self) -> str:
        return self.summary()

    def summary(self) -> str:
        """Short text for lists, e.g. "School of Computing · Intake October 2024"."""
        schools = [school.name for school in self.schools.all()]
        programmes = [programme.name for programme in self.programmes.all()]
        intakes = [intake.name for intake in self.intakes.all()]
        courses = [course.code for course in self.courses.all()]
        sections = [
            f"{section.course.code} Section {section.code}"
            for section in self.sections.select_related("course")
        ]
        parts = []
        if schools:
            parts.append(" or ".join(schools))
        if programmes:
            parts.append(" or ".join(programmes))
        if intakes:
            parts.append(("Intake " if len(intakes) == 1 else "Intakes ") + " or ".join(intakes))
        if courses:
            parts.append(" or ".join(courses))
        if sections:
            parts.append(" or ".join(sections))
        return " · ".join(parts) or "All students"
