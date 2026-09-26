"""What the API returns for each academic item (read-only)."""

from rest_framework import serializers

from .models import Intake, Programme, School


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
