"""Read-only lists of AIU's academic structure (used by website dropdowns).

- Only active items are returned.
- Login is required (the project default, IsAuthenticated).
- Not paginated: these lists are short and dropdowns need every item.
"""

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import exceptions, generics

from .models import Intake, Programme, School
from .serializers import IntakeSerializer, ProgrammeSerializer, SchoolSerializer


@extend_schema(tags=["academics"])
class SchoolListView(generics.ListAPIView):
    serializer_class = SchoolSerializer
    pagination_class = None
    queryset = School.objects.filter(is_active=True)


@extend_schema(
    tags=["academics"],
    parameters=[
        OpenApiParameter(
            "school",
            OpenApiTypes.INT,
            description="Only programmes of this school (id).",
            required=False,
        )
    ],
)
class ProgrammeListView(generics.ListAPIView):
    serializer_class = ProgrammeSerializer
    pagination_class = None

    def get_queryset(self):
        queryset = Programme.objects.filter(is_active=True, school__is_active=True)
        school = self.request.query_params.get("school")
        if school is not None:
            if not school.isdigit():
                raise exceptions.ValidationError({"school": ["Must be a school id (a number)."]})
            queryset = queryset.filter(school_id=int(school))
        return queryset


@extend_schema(tags=["academics"])
class IntakeListView(generics.ListAPIView):
    serializer_class = IntakeSerializer
    pagination_class = None
    queryset = Intake.objects.filter(is_active=True)
