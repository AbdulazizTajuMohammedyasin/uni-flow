"""Staff area: manage schools, programmes and intakes (/api/v1/manage/academics/).

University admins and super admins only. Nothing is deleted: set is_active to false to
hide an item from the website's lists (students' profiles keep pointing at it).
"""

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import filters, viewsets

from apps.accounts.capabilities import HasCapability

from .models import Intake, Programme, School
from .serializers import ManageIntakeSerializer, ManageProgrammeSerializer, ManageSchoolSerializer


class ManageAcademicsViewSet(viewsets.ModelViewSet):
    """Shared setup: list (incl. inactive), view, create, edit. No deleting."""

    permission_classes = [HasCapability("academics.manage")]
    http_method_names = ["get", "post", "patch"]
    filter_backends = [filters.SearchFilter]
    search_fields = ["code", "name"]


@extend_schema(tags=["manage: academics"])
class ManageSchoolViewSet(ManageAcademicsViewSet):
    queryset = School.objects.all()
    serializer_class = ManageSchoolSerializer


@extend_schema_view(
    list=extend_schema(
        parameters=[OpenApiParameter("school", OpenApiTypes.INT, description="Only this school's.")]
    )
)
@extend_schema(tags=["manage: academics"])
class ManageProgrammeViewSet(ManageAcademicsViewSet):
    serializer_class = ManageProgrammeSerializer

    def get_queryset(self):
        programmes = Programme.objects.all()
        school = self.request.query_params.get("school")
        if school and school.isdigit():
            programmes = programmes.filter(school_id=int(school))
        return programmes


@extend_schema(tags=["manage: academics"])
class ManageIntakeViewSet(ManageAcademicsViewSet):
    queryset = Intake.objects.all()
    serializer_class = ManageIntakeSerializer
