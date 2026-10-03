"""What the timetable API accepts and returns."""

from rest_framework import serializers

from apps.academics.models import Course

from .models import ClassMeeting, CourseSection


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


class SectionSerializer(serializers.ModelSerializer):
    """A section with its course and weekly classes."""

    course = CourseBriefSerializer(read_only=True)
    meetings = MeetingSerializer(many=True, read_only=True)

    class Meta:
        model = CourseSection
        fields = ["id", "course", "code", "term", "lecturer_name", "source", "meetings"]


class JoinSectionSerializer(serializers.Serializer):
    """POST timetable/my-sections/ — {"section": <id>}."""

    section = serializers.PrimaryKeyRelatedField(queryset=CourseSection.objects.all())


class AddSectionSerializer(serializers.Serializer):
    """POST timetable/sections/ — add a class that is not in UniFlow yet."""

    course_code = serializers.CharField(max_length=20)
    course_name = serializers.CharField(max_length=200)
    section = serializers.CharField(max_length=20)
    meetings = MeetingSerializer(many=True, allow_empty=False)


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


class DaySerializer(serializers.Serializer):
    date = serializers.DateField()
    weekday = serializers.IntegerField(help_text="0 = Monday … 6 = Sunday")
    classes = ClassSlotSerializer(many=True)


class TermBriefSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()


class TimetableDaysSerializer(serializers.Serializer):
    """GET timetable/today/ (one day) and timetable/week/ (Monday to Sunday)."""

    term = TermBriefSerializer(allow_null=True)
    days = DaySerializer(many=True)
