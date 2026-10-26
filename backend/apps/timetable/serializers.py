"""What the timetable API accepts and returns."""

from rest_framework import serializers

from apps.academics.models import Course, Term

from . import changes
from .models import ClassChange, ClassMeeting, CourseSection


class MeetingSerializer(serializers.ModelSerializer):
    weekday_label = serializers.CharField(source="get_weekday_display", read_only=True)

    class Meta:
        model = ClassMeeting
        fields = [
            "weekday",
            "weekday_label",
            "start_time",
            "end_time",
            "meeting_type",
            "building",
            "room",
        ]

    def validate(self, attrs):
        if attrs["end_time"] <= attrs["start_time"]:
            raise serializers.ValidationError({"end_time": "Must be after the start time."})
        return attrs


class CourseBriefSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ["id", "code", "name"]


class SemesterSerializer(serializers.Serializer):
    """A term as students see it (estimated: dates worked out from last year's calendar)."""

    id = serializers.IntegerField()
    name = serializers.CharField()
    starts_on = serializers.DateField()
    ends_on = serializers.DateField()
    estimated = serializers.BooleanField()


class SectionSerializer(serializers.ModelSerializer):
    """A section with its course, term and weekly classes."""

    course = CourseBriefSerializer(read_only=True)
    meetings = MeetingSerializer(many=True, read_only=True)
    semester = SemesterSerializer(source="term", read_only=True)

    class Meta:
        model = CourseSection
        fields = ["id", "course", "code", "term", "semester", "lecturer_name", "source", "meetings"]


class SemestersSerializer(serializers.Serializer):
    """GET timetable/semesters/ — the two terms classes can be added to."""

    current = SemesterSerializer(allow_null=True)
    next = SemesterSerializer(allow_null=True)


class MoveSectionsSerializer(serializers.Serializer):
    """POST timetable/my-sections/move/ — move my classes out of a term that has ended."""

    from_term = serializers.PrimaryKeyRelatedField(queryset=Term.objects.all())


class JoinSectionSerializer(serializers.Serializer):
    """POST timetable/my-sections/ — {"section": <id>}."""

    section = serializers.PrimaryKeyRelatedField(queryset=CourseSection.objects.all())


class AddSectionSerializer(serializers.Serializer):
    """POST timetable/sections/ — add a class that is not in UniFlow yet."""

    course_code = serializers.CharField(max_length=20)
    course_name = serializers.CharField(max_length=200)
    section = serializers.CharField(max_length=20)
    meetings = MeetingSerializer(many=True, allow_empty=False)
    semester = serializers.ChoiceField(choices=["current", "next"], default="current")


class ChangeFlagSerializer(serializers.Serializer):
    """A class change on this class: confirmed (applied) or pending (not answered yet)."""

    id = serializers.IntegerField()
    kind = serializers.ChoiceField(choices=ClassChange.Kind.choices)
    status = serializers.ChoiceField(choices=["confirmed", "pending"])


class ClassSlotSerializer(serializers.Serializer):
    """One class on one day."""

    section_id = serializers.IntegerField()
    course_code = serializers.CharField()
    course_name = serializers.CharField()
    section_code = serializers.CharField()
    lecturer_name = serializers.CharField()
    start_time = serializers.TimeField(format="%H:%M")
    end_time = serializers.TimeField(format="%H:%M")
    meeting_type = serializers.CharField()
    building = serializers.CharField()
    room = serializers.CharField()
    change = ChangeFlagSerializer(allow_null=True)


class DaySerializer(serializers.Serializer):
    date = serializers.DateField()
    weekday = serializers.IntegerField(help_text="0 = Monday … 6 = Sunday")
    classes = ClassSlotSerializer(many=True)


class TermBriefSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    starts_on = serializers.DateField()
    ends_on = serializers.DateField()


class TimetableDaysSerializer(serializers.Serializer):
    """GET timetable/today/ (one day) and timetable/week/ (Monday to Sunday)."""

    term = TermBriefSerializer(allow_null=True)
    days = DaySerializer(many=True)


class EvidenceSerializer(serializers.Serializer):
    """The message a change was found in (the quote stays after the 60-day clean-up)."""

    quote = serializers.CharField()
    group = serializers.CharField(source="message.source.title")
    sender_name = serializers.CharField(source="message.sender_name")
    sent_at = serializers.DateTimeField(source="message.sent_at")


class DecideChangeSerializer(serializers.Serializer):
    """POST timetable/changes/{id}/confirm/: for that week only, or for every week."""

    every_week = serializers.BooleanField(default=False)


class ClassChangeSerializer(serializers.ModelSerializer):
    """GET timetable/changes/ — a proposed change, the original class and my answer."""

    course_code = serializers.CharField(source="section.course.code")
    course_name = serializers.CharField(source="section.course.name")
    section_code = serializers.CharField(source="section.code")
    title = serializers.CharField(source="insight.title")
    summary = serializers.CharField(source="insight.summary")
    not_confirmed = serializers.BooleanField(
        source="insight.is_unconfirmed", help_text="The AI wasn't sure about it."
    )
    old_start = serializers.TimeField(
        source="meeting.start_time", format="%H:%M", allow_null=True, default=None
    )
    old_end = serializers.TimeField(
        source="meeting.end_time", format="%H:%M", allow_null=True, default=None
    )
    old_room = serializers.CharField(source="meeting.room", allow_null=True, default=None)
    new_start = serializers.TimeField(format="%H:%M", allow_null=True)
    new_end = serializers.TimeField(format="%H:%M", allow_null=True)
    my_status = serializers.ChoiceField(choices=["pending", "confirmed", "rejected"])
    can_repeat = serializers.SerializerMethodField(
        help_text="A moved class or room change: it can be confirmed for every week."
    )
    every_week = serializers.BooleanField(
        source="my_every_week", help_text="I confirmed it for every week, not only that week."
    )
    evidence = EvidenceSerializer(source="insight.evidence.all", many=True)

    def get_can_repeat(self, change) -> bool:
        return changes.can_repeat(change)

    class Meta:
        model = ClassChange
        fields = [
            "id",
            "kind",
            "course_code",
            "course_name",
            "section_code",
            "title",
            "summary",
            "not_confirmed",
            "date",
            "old_start",
            "old_end",
            "old_room",
            "new_date",
            "new_start",
            "new_end",
            "new_room",
            "my_status",
            "can_repeat",
            "every_week",
            "evidence",
        ]
