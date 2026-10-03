"""Read-only lists of AIU's academic structure (used by website dropdowns).

- Only active items are returned (terms have no active flag: all are listed, newest first).
- Login is required (the project default, IsAuthenticated).
- Not paginated: these lists are short and dropdowns need every item.
"""

from django.utils import timezone
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import exceptions, filters, generics

from .models import Course, Intake, Programme, School, Term
from .serializers import (
    CourseSerializer,
    IntakeSerializer,
    ProgrammeSerializer,
    SchoolSerializer,
    TermSerializer,
)


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
        return filter_by_school(queryset, self.request)


def filter_by_school(queryset, request):
    """Apply the optional ?school=<id> filter (400 if it is not a number)."""
    school = request.query_params.get("school")
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


@extend_schema(
    tags=["academics"],
    parameters=[
        OpenApiParameter(
            "school",
            OpenApiTypes.INT,
            description="Only courses of this school (id).",
            required=False,
        )
    ],
)
class CourseListView(generics.ListAPIView):
    """Active courses of active schools. `?search=` matches the code or name."""

    serializer_class = CourseSerializer
    pagination_class = None
    filter_backends = [filters.SearchFilter]
    search_fields = ["code", "name"]

    def get_queryset(self):
        queryset = Course.objects.filter(is_active=True, school__is_active=True)
        return filter_by_school(queryset, self.request)


CALENDAR_PARAMETER = OpenApiParameter(
    "calendar",
    OpenApiTypes.STR,
    description="undergraduate (default) or foundation.",
    required=False,
)


def requested_calendar(request) -> str:
    calendar = request.query_params.get("calendar", Term.Calendar.UNDERGRADUATE)
    if calendar not in Term.Calendar.values:
        raise exceptions.ValidationError({"calendar": ["Must be undergraduate or foundation."]})
    return calendar


@extend_schema(tags=["academics"], parameters=[CALENDAR_PARAMETER])
class TermListView(generics.ListAPIView):
    """Terms of one calendar (undergraduate by default), newest first."""

    serializer_class = TermSerializer
    pagination_class = None

    def get_queryset(self):
        return Term.objects.filter(calendar=requested_calendar(self.request))


@extend_schema(tags=["academics"], parameters=[CALENDAR_PARAMETER])
class CurrentTermView(generics.RetrieveAPIView):
    """The current term of one calendar, worked out from today's date (404 if none)."""

    serializer_class = TermSerializer

    def get_object(self):
        calendar = requested_calendar(self.request)
        term = Term.current(calendar, timezone.localdate())
        if term is None:
            raise exceptions.NotFound("No terms have been added yet.")
        return term
