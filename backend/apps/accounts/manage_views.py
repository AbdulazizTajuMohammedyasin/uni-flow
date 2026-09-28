"""Staff area: user management for super admins (/api/v1/manage/users/)."""

from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import filters, mixins, status, viewsets
from rest_framework.response import Response

from .capabilities import HasCapability
from .models import User
from .serializers import (
    CreateStaffUserSerializer,
    ManagedUserSerializer,
    UpdateStaffUserSerializer,
)


@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter("role", str, description="Only users with this role."),
            OpenApiParameter("school", int, description="Only staff of this school (id)."),
        ]
    ),
    create=extend_schema(request=CreateStaffUserSerializer, responses={201: ManagedUserSerializer}),
    partial_update=extend_schema(
        request=UpdateStaffUserSerializer, responses={200: ManagedUserSerializer}
    ),
)
@extend_schema(tags=["manage: users"])
class ManageUserViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    """List/search users, create staff accounts, change role/school, suspend. No deleting."""

    permission_classes = [HasCapability("users.manage")]
    serializer_class = ManagedUserSerializer
    http_method_names = ["get", "post", "patch"]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["email", "full_name"]
    ordering_fields = ["email", "full_name", "date_joined"]
    ordering = ["email"]

    def get_queryset(self):
        users = User.objects.select_related("staff_profile").all()
        role = self.request.query_params.get("role")
        school = self.request.query_params.get("school")
        if role:
            users = users.filter(role=role)
        if school and school.isdigit():
            users = users.filter(staff_profile__school_id=int(school))
        return users

    def get_serializer_class(self):
        if self.action == "create":
            return CreateStaffUserSerializer
        if self.action == "partial_update":
            return UpdateStaffUserSerializer
        return ManagedUserSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(ManagedUserSerializer(user).data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_object(), data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(ManagedUserSerializer(user).data)
