from django.db import DatabaseError, connection
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import exceptions, serializers, status
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

HealthResponse = inline_serializer(
    name="HealthResponse",
    fields={"status": serializers.CharField(), "db": serializers.CharField()},
)


@extend_schema(responses={200: HealthResponse, 503: HealthResponse}, tags=["system"])
@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
def health(request):
    """Public liveness check for uptime monitors: is the API up and can it reach MySQL?"""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except DatabaseError:
        return Response(
            {"status": "error", "db": "unavailable"},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )
    return Response({"status": "ok", "db": "ok"})


@extend_schema(exclude=True)
@api_view(["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"])
@authentication_classes([])
@permission_classes([AllowAny])
def api_not_found(request, *args, **kwargs):
    """Catch-all for unknown /api/v1/ paths, so they get the JSON error format, not HTML."""
    raise exceptions.NotFound("This API endpoint does not exist.")
