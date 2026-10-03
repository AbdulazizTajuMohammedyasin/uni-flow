"""Student timetable API (/api/v1/timetable/): browse sections, my sections, add a class.

Students only ever change their own enrolments; shared sections created by hand are
never edited afterwards by students (see services.py).
"""

from django.db.models import Prefetch
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import exceptions, filters, generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from . import services
from .models import ClassMeeting, CourseSection, SectionEnrollment
from .serializers import AddSectionSerializer, JoinSectionSerializer, SectionSerializer


def id_param(request, name: str) -> int | None:
    """An optional ?name=<id> filter (400 if it is not a number)."""
    value = request.query_params.get(name)
    if value is None:
        return None
    if not value.isdigit():
        raise exceptions.ValidationError({name: ["Must be an id (a number)."]})
    return int(value)


def sections_with_details():
    return CourseSection.objects.select_related("course").prefetch_related(
        Prefetch("meetings", queryset=ClassMeeting.objects.order_by("weekday", "start_time"))
    )


@extend_schema_view(
    get=extend_schema(
        parameters=[
            OpenApiParameter("course", OpenApiTypes.INT, description="Only this course (id)."),
            OpenApiParameter("school", OpenApiTypes.INT, description="Only this school (id)."),
        ]
    ),
    post=extend_schema(request=AddSectionSerializer, responses={201: SectionSerializer}),
)
@extend_schema(tags=["timetable"])
class SectionListView(generics.ListCreateAPIView):
    """GET: sections of the current term (`?search=` on course code or name).
    POST: add a class that is not in UniFlow yet, and join it."""

    serializer_class = SectionSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ["course__code", "course__name"]

    def get_queryset(self):
        term = services.current_term_for(self.request.user)
        sections = sections_with_details().filter(term=term, is_active=True)
        if (course := id_param(self.request, "course")) is not None:
            sections = sections.filter(course_id=course)
        if (school := id_param(self.request, "school")) is not None:
            sections = sections.filter(course__school_id=school)
        return sections.order_by("course__code", "code")

    def create(self, request, *args, **kwargs):
        serializer = AddSectionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        section, created = services.add_section_by_hand(
            request.user,
            course_code=data["course_code"],
            course_name=data["course_name"],
            section_code=data["section"],
            meetings=data["meetings"],
        )
        body = SectionSerializer(sections_with_details().get(pk=section.pk)).data
        return Response(body, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


@extend_schema_view(
    post=extend_schema(request=JoinSectionSerializer, responses={201: SectionSerializer}),
)
@extend_schema(tags=["timetable"])
class MySectionsView(generics.ListCreateAPIView):
    """GET: my sections this term. POST {"section": id}: join a section."""

    serializer_class = SectionSerializer
    pagination_class = None

    def get_queryset(self):
        services.require_student(self.request.user)
        term = services.current_term_for(self.request.user)
        return (
            sections_with_details()
            .filter(term=term, enrollments__user=self.request.user)
            .order_by("course__code", "code")
        )

    def create(self, request, *args, **kwargs):
        serializer = JoinSectionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        section = serializer.validated_data["section"]
        services.join_section(request.user, section)
        body = SectionSerializer(sections_with_details().get(pk=section.pk)).data
        return Response(body, status=status.HTTP_201_CREATED)


@extend_schema(tags=["timetable"], responses={204: None})
class MySectionDeleteView(APIView):
    """DELETE timetable/my-sections/{section_id}/ — leave a section."""

    def delete(self, request, section_id):
        services.require_student(request.user)
        enrollment = generics.get_object_or_404(
            SectionEnrollment, user=request.user, section_id=section_id
        )
        enrollment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
