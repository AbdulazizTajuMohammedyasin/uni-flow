"""Applying a list of classes (read by the AI, or from a file) to the shared timetable.

Rules (docs/03-data-model.md, "Import service"):
- Missing courses, sections and weekly classes are created (shared by everyone).
- Existing sections are never changed: if an import shows different weekly classes, the
  difference is reported (for the admin) and the existing classes stay.
- Optionally the student is enrolled in every section of the import.
- dry_run=True works everything out and saves nothing (a preview).
"""

import re
from dataclasses import asdict, dataclass, field
from datetime import time

from django.db import transaction

from apps.academics.models import Course, School, Term

from .models import ClassMeeting, CourseSection, SectionEnrollment

WEEKDAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
MEETING_TYPES = {"lecture", "tutorial", "lab", "other"}


@dataclass
class MeetingRow:
    weekday: int  # 0 = Monday
    start_time: time
    end_time: time
    meeting_type: str = "lecture"
    room: str = ""

    def key(self):
        return (self.weekday, self.start_time, self.end_time, self.room.strip().upper())


@dataclass
class SectionRow:
    course_code: str
    course_name: str
    section_code: str
    lecturer_name: str = ""
    meetings: list[MeetingRow] = field(default_factory=list)

    @property
    def label(self) -> str:
        return f"{self.course_code} Section {self.section_code}"


@dataclass
class ImportReport:
    created_courses: list[str] = field(default_factory=list)
    created_sections: list[str] = field(default_factory=list)
    existing_sections: list[str] = field(default_factory=list)
    differences: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    enrolled: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return asdict(self)


# --- Rows <-> plain JSON (stored on imports between reading and confirming) ---------


def rows_to_json(rows: list[SectionRow]) -> list[dict]:
    return [
        {
            "course_code": row.course_code,
            "course_name": row.course_name,
            "section": row.section_code,
            "lecturer": row.lecturer_name,
            "meetings": [
                {
                    "day": WEEKDAYS[m.weekday],
                    "start": m.start_time.strftime("%H:%M"),
                    "end": m.end_time.strftime("%H:%M"),
                    "type": m.meeting_type,
                    "room": m.room,
                }
                for m in row.meetings
            ],
        }
        for row in rows
    ]


def section_code(value) -> str:
    """ "Grp A", "Group A", "Section A" and "Sec. A" are all section "A"."""
    code = re.sub(r"^(GROUP|GRP|SECTION|SEC)\.?\s*", "", str(value).strip().upper())
    return code[:20]


def _time(value) -> time | None:
    try:
        hours, minutes = str(value).strip().split(":")[:2]
        return time(int(hours), int(minutes))
    except (ValueError, TypeError):
        return None


def rows_from_json(items: list[dict]) -> list[SectionRow]:
    """Turn JSON (from the AI or a student's edits) into rows, dropping anything invalid:
    a class without a course code, an unknown day, or a time that ends before it starts."""
    rows = []
    for item in items or []:
        code = str(item.get("course_code", "")).strip().upper().replace(" ", "")[:20]
        if not code:
            continue
        meetings = []
        for meeting in item.get("meetings") or []:
            day = str(meeting.get("day", "")).strip().lower()
            start, end = _time(meeting.get("start")), _time(meeting.get("end"))
            if day not in WEEKDAYS or start is None or end is None or end <= start:
                continue
            kind = str(meeting.get("type", "lecture")).strip().lower()
            meetings.append(
                MeetingRow(
                    weekday=WEEKDAYS.index(day),
                    start_time=start,
                    end_time=end,
                    meeting_type=kind if kind in MEETING_TYPES else "other",
                    room=str(meeting.get("room", "")).strip()[:50],
                )
            )
        rows.append(
            SectionRow(
                course_code=code,
                course_name=str(item.get("course_name", "")).strip()[:200] or code,
                section_code=section_code(item.get("section", "")) or "1",
                lecturer_name=str(item.get("lecturer", "")).strip()[:150],
                meetings=meetings,
            )
        )
    return rows


# --- Applying -------------------------------------------------------------------------


def apply_timetable_rows(
    term: Term,
    rows: list[SectionRow],
    *,
    user,
    school: School | None,
    source: str = CourseSection.Source.AI_IMPORT,
    enroll: bool = False,
    dry_run: bool = False,
) -> ImportReport:
    """Create what's missing from `rows` in `term`; never change what exists."""
    report = ImportReport()
    with transaction.atomic():
        for row in rows:
            course = Course.objects.filter(code=row.course_code).first()
            if course is None:
                if school is None:
                    report.errors.append(
                        f"{row.course_code}: unknown course and no school to add it to."
                    )
                    continue
                course = Course.objects.create(
                    school=school, code=row.course_code, name=row.course_name
                )
                report.created_courses.append(row.course_code)

            section, created = CourseSection.objects.get_or_create(
                course=course,
                term=term,
                code=row.section_code,
                defaults={
                    "lecturer_name": row.lecturer_name,
                    "source": source,
                    "created_by": user,
                    "updated_by": user,
                },
            )
            if created:
                ClassMeeting.objects.bulk_create(
                    ClassMeeting(
                        section=section,
                        weekday=m.weekday,
                        start_time=m.start_time,
                        end_time=m.end_time,
                        meeting_type=m.meeting_type,
                        room=m.room,
                        updated_by=user,
                    )
                    for m in row.meetings
                )
                report.created_sections.append(row.label)
            else:
                report.existing_sections.append(row.label)
                existing = {
                    (m.weekday, m.start_time, m.end_time, m.room.strip().upper())
                    for m in section.meetings.all()
                }
                if row.meetings and existing != {m.key() for m in row.meetings}:
                    report.differences.append(
                        f"{row.label}: weekly classes differ from the import (kept existing)."
                    )

            if enroll and user is not None:
                SectionEnrollment.objects.get_or_create(user=user, section=section)
                report.enrolled.append(row.label)

        if dry_run:
            transaction.set_rollback(True)
    return report
