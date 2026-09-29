"""The "audience" part of a post, as sent and received by the API.

Example: {"schools": [], "programmes": [], "intakes": [12], "summary": "Intake October 2024"}
Content serializers (announcements, events, ...) use this as a nested field.
"""

from rest_framework import serializers

from apps.academics.models import Intake, Programme, School

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
    summary = serializers.CharField(read_only=True)

    class Meta:
        model = Audience
        fields = ["schools", "programmes", "intakes", "summary"]
