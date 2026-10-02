"""Small read-only account endpoints that Djoser does not provide."""

from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import InfoType, Interest

ChoiceList = serializers.ListField(
    child=inline_serializer(
        "Choice", {"value": serializers.CharField(), "label": serializers.CharField()}
    )
)


@extend_schema(
    tags=["auth"],
    responses=inline_serializer(
        "PreferenceChoices", {"interests": ChoiceList, "info_types": ChoiceList}
    ),
)
class PreferenceChoicesView(APIView):
    """GET /api/v1/auth/preferences/choices/ — the options for the interests and
    information-type pickers (onboarding and profile)."""

    def get(self, request):
        def as_list(choices):
            return [{"value": value, "label": label} for value, label in choices.choices]

        return Response({"interests": as_list(Interest), "info_types": as_list(InfoType)})
