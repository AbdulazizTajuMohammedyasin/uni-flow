"""The "audience" part of a post, as sent and received by the API.

Example: {"schools": [], "programmes": [], "intakes": [12], "courses": [], "sections": [],
          "summary": "Intake October 2024"}
Insight serializers use this as a nested field.
"""

from rest_framework import serializers

from apps.academics.models import Course, Intake, Programme, School
from apps.timetable.models import CourseSection

from .models import Audience


class AudienceSerializer(serializers.ModelSerializer):
    # Only active items can be chosen.
    schools = serializers.PrimaryKeyRelatedField(
        many=True, required=False, queryset=School.objects.filter(is_active=True)
    )
    programmes = serializers.PrimaryKeyRelatedField(
        many=True, required=False, queryset=Programme.objects.filter(is_active=True)
    )
    intakes = serializers.PrimaryKeyRelatedField(
        many=True, required=False, queryset=Intake.objects.filter(is_active=True)
    )
    courses = serializers.PrimaryKeyRelatedField(
        many=True, required=False, queryset=Course.objects.filter(is_active=True)
    )
    sections = serializers.PrimaryKeyRelatedField(
        many=True, required=False, queryset=CourseSection.objects.filter(is_active=True)
    )
    semester_min = serializers.IntegerField(
        min_value=1, max_value=15, allow_null=True, required=False
    )
    semester_max = serializers.IntegerField(
        min_value=1, max_value=15, allow_null=True, required=False
    )
    summary = serializers.CharField(read_only=True)

    class Meta:
        model = Audience
        fields = [
            "schools",
            "programmes",
            "intakes",
            "courses",
            "sections",
            "semester_min",
            "semester_max",
            "summary",
        ]

    def validate(self, attrs):
        low, high = attrs.get("semester_min"), attrs.get("semester_max")
        if low and high and high < low:
            raise serializers.ValidationError(
                {"semester_max": "Must be the same as or after the first semester."}
            )
        return attrs
