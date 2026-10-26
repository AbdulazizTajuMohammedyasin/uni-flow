"""Class changes found by the AI (docs/12-intelligence.md, "Timetable intelligence").

- propose_changes: a published timetable insight becomes a proposal for each section.
- retract_changes: the insight was taken back, so its proposals disappear.
- decide: a student confirms or rejects a proposal (only for their own timetable). A moved
  class or a room change can be confirmed for every week, not only the week it was found for.
- apply_changes: the student's Today/Week = weekly classes + the changes they confirmed;
  changes they haven't answered yet are flagged on the class.

The weekly classes (ClassMeeting) are never edited.
"""

from datetime import date, datetime, time

from django.db.models import OuterRef, Q, QuerySet, Subquery, Value
from django.db.models.functions import Coalesce
from django.utils import timezone

from apps.publishing.models import Status as PublishStatus

from .models import ClassChange, ClassChangeConfirmation, ClassMeeting, CourseSection

PENDING = "pending"  # the student hasn't answered yet

# Changes a student can confirm for every week (a cancellation or an extra session is one day).
REPEATABLE = {ClassChange.Kind.CLASS_MOVED, ClassChange.Kind.ROOM_CHANGED}


def _time(value: str) -> time | None:
    return time.fromisoformat(value) if value else None


def _meeting_for(section: CourseSection, day: date, data: dict) -> ClassMeeting | None:
    """The section's weekly class on that weekday (at the old start time, if given)."""
    meetings = section.meetings.filter(weekday=day.weekday())
    if data.get("old_start"):
        meetings = meetings.filter(start_time=data["old_start"])
    return meetings.first() if len(meetings) == 1 else None


def propose_changes(insight) -> list[ClassChange]:
    """Create (or bring back) one proposal per section of a published timetable insight."""
    data = insight.data or {}
    if insight.kind not in ClassChange.Kind.values or not data.get("section_ids"):
        return []
    day = date.fromisoformat(data["date"])
    new_date = date.fromisoformat(data["new_date"]) if data.get("new_date") else None
    changes = []
    for section in CourseSection.objects.filter(pk__in=data["section_ids"]):
        meeting = (
            None
            if insight.kind == ClassChange.Kind.EXTRA_SESSION
            else _meeting_for(section, day, data)
        )
        new_start, new_end = _time(data.get("new_start", "")), _time(data.get("new_end", ""))
        if meeting and new_start and not new_end:  # "moved to 2 PM": same length as before
            length = datetime.combine(day, meeting.end_time) - datetime.combine(
                day, meeting.start_time
            )
            new_end = (datetime.combine(day, new_start) + length).time()
        change, _ = ClassChange.objects.update_or_create(
            insight=insight,
            section=section,
            defaults={
                "kind": insight.kind,
                "meeting": meeting,
                "date": day,
                "new_date": new_date if new_date != day else None,
                "new_start": new_start,
                "new_end": new_end,
                "new_room": data.get("new_room", "")[:50],
                "status": ClassChange.Status.PROPOSED,
            },
        )
        changes.append(change)
    return changes


def retract_changes(insight) -> int:
    """The insight was taken back: its proposals leave every timetable."""
    return ClassChange.objects.filter(insight=insight).update(
        status=ClassChange.Status.RETRACTED, updated_at=timezone.now()
    )


def changes_for(user) -> QuerySet[ClassChange]:
    """Live proposals for the student's sections, with their answer as `my_status`."""
    answer = ClassChangeConfirmation.objects.filter(change=OuterRef("pk"), user=user)
    return (
        ClassChange.objects.filter(
            status=ClassChange.Status.PROPOSED,
            insight__status=PublishStatus.PUBLISHED,
            section__enrollments__user=user,
        )
        .annotate(
            my_status=Coalesce(Subquery(answer.values("status")[:1]), Value(PENDING)),
            my_every_week=Coalesce(Subquery(answer.values("every_week")[:1]), Value(False)),
        )
        .select_related("section__course", "meeting", "insight")
    )


def can_repeat(change: ClassChange) -> bool:
    """Whether the change can be confirmed for every week: a moved class or a room change of
    a weekly class."""
    return change.kind in REPEATABLE and change.meeting_id is not None


def decide(
    user, change: ClassChange, confirmed: bool, every_week: bool = False
) -> ClassChangeConfirmation:
    """Save the student's answer (they can change their mind later). `every_week`: the change
    applies every week from its date until the term ends, not only that week."""
    status = (
        ClassChangeConfirmation.Status.CONFIRMED
        if confirmed
        else ClassChangeConfirmation.Status.REJECTED
    )
    answer, _ = ClassChangeConfirmation.objects.update_or_create(
        change=change,
        user=user,
        defaults={
            "status": status,
            "every_week": confirmed and every_week and can_repeat(change),
            "decided_at": timezone.now(),
        },
    )
    return answer


def _flag(change: ClassChange) -> dict:
    return {"id": change.id, "kind": change.kind, "status": change.my_status}


def _extra_slot(change: ClassChange) -> dict:
    """A class that isn't in the weekly timetable (an extra session or a moved class)."""
    section, meeting = change.section, change.meeting
    return {
        "section_id": section.id,
        "meeting_id": None,
        "course_code": section.course.code,
        "course_name": section.course.name,
        "section_code": section.code,
        "lecturer_name": section.lecturer_name,
        "start_time": change.new_start or meeting.start_time,
        "end_time": change.new_end or meeting.end_time,
        "meeting_type": meeting.meeting_type if meeting else ClassMeeting.MeetingType.OTHER,
        "building": meeting.building if meeting else "",
        "room": change.new_room or (meeting.room if meeting else ""),
        "change": _flag(change),
    }


def _weeks(change: ClassChange, days: dict[date, list[dict]]) -> list[date]:
    """The days among `days` a change applies to: its own date, plus the same weekday of the
    later weeks when it was confirmed for every week (a weekly class belongs to one term, so
    it stops when the term ends)."""
    if not change.my_every_week:
        return [change.date]
    return [day for day in days if day >= change.date and day.weekday() == change.date.weekday()]


def apply_changes(user, days: dict[date, list[dict]]) -> None:
    """Show the student's changes on `days` (date -> that day's class slots, edited here).

    Confirmed: cancelled classes are flagged, moves and room changes are applied (each week,
    when confirmed for every week), extra sessions are added. Not answered yet: the class is
    only flagged. Rejected: nothing. A later change wins over an earlier one.
    """
    every_week = Q(
        my_status=ClassChangeConfirmation.Status.CONFIRMED,
        my_every_week=True,
        date__lte=max(days),
    )
    changes = changes_for(user).filter(
        Q(date__in=list(days)) | Q(new_date__in=list(days)) | every_week
    )
    for change in changes.exclude(my_status=ClassChangeConfirmation.Status.REJECTED):
        for on in _weeks(change, days):
            _apply(change, on, days)
    for slots in days.values():
        slots.sort(key=lambda s: s["start_time"])


def _apply(change: ClassChange, on: date, days: dict[date, list[dict]]) -> None:
    """Show one change on the class of day `on` (the change's date, or a later week)."""
    confirmed = change.my_status == ClassChangeConfirmation.Status.CONFIRMED
    slots = days.get(on, [])
    slot = next((s for s in slots if s["meeting_id"] == change.meeting_id), None)
    if slot is not None and change.meeting_id is not None:
        slot["change"] = _flag(change)
    if not confirmed:
        return

    if change.kind == ClassChange.Kind.EXTRA_SESSION:
        if change.new_start and change.new_end and on in days:
            slots.append(_extra_slot(change))
    elif change.kind == ClassChange.Kind.CLASS_MOVED and change.new_date:
        new_day = on + (change.new_date - change.date)
        if slot is not None:  # it leaves this day...
            slots.remove(slot)
        if new_day in days and change.meeting:  # ...and appears on the new one
            days[new_day].append(_extra_slot(change))
    elif slot is not None and change.kind == ClassChange.Kind.CLASS_MOVED:
        slot["start_time"] = change.new_start or slot["start_time"]
        slot["end_time"] = change.new_end or slot["end_time"]
        slot["room"] = change.new_room or slot["room"]
    elif slot is not None and change.kind == ClassChange.Kind.ROOM_CHANGED:
        slot["room"] = change.new_room or slot["room"]
    # class_cancelled: the class stays, flagged as cancelled, so the student sees why.
