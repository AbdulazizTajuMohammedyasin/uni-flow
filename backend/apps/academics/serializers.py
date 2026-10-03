"""What the API returns for each academic item (read lists, and the staff-area versions)."""

from rest_framework import serializers

from .models import Course, Intake, Programme, School, Term


class SchoolSerializer(serializers.ModelSerializer):
    class Meta:
        model = School
        fields = ["id", "code", "name"]


class ProgrammeSerializer(serializers.ModelSerializer):
    level_label = serializers.CharField(source="get_level_display", read_only=True)

    class Meta:
        model = Programme
        fields = ["id", "code", "name", "level", "level_label", "school"]


class IntakeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Intake
        fields = ["id", "code", "name", "start_date"]


class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ["id", "code", "name", "school"]


class TermSerializer(serializers.ModelSerializer):
    class Meta:
        model = Term
        fields = [
            "id",
            "calendar",
            "name",
            "academic_session",
            "number",
            "starts_on",
            "ends_on",
        ]


# --- Staff area: manage the lists (/api/v1/manage/academics/) -------------------------


class ManageSchoolSerializer(serializers.ModelSerializer):
    class Meta:
        model = School
        fields = ["id", "code", "name", "is_active"]


class ManageProgrammeSerializer(serializers.ModelSerializer):
    level_label = serializers.CharField(source="get_level_display", read_only=True)

    class Meta:
        model = Programme
        fields = ["id", "code", "name", "level", "level_label", "school", "is_active"]


class ManageIntakeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Intake
        fields = ["id", "code", "name", "start_date", "is_active"]
