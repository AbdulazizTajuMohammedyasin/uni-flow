"""Sources API (/api/v1/sources/): my groups, a group for pasted messages, pasting, and
uploading a WhatsApp "Export chat" file. Connecting real groups comes in M6."""

from django.db.models import Count
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import generics, status
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from . import services
from .models import Source
from .serializers import (
    CreateSourceSerializer,
    ExportSerializer,
    ImportResultSerializer,
    PasteSerializer,
    SourceSerializer,
)


def import_result(added: int, already_stored: int) -> Response:
    data = {"added": added, "already_stored": already_stored}
    return Response(ImportResultSerializer(data).data, status=status.HTTP_201_CREATED)


@extend_schema_view(
    post=extend_schema(request=CreateSourceSerializer, responses={201: SourceSerializer}),
)
@extend_schema(tags=["sources"])
class SourceListView(generics.ListCreateAPIView):
    """GET: the groups I added. POST: a group for pasted or uploaded messages."""

    serializer_class = SourceSerializer
    pagination_class = None

    def get_queryset(self):
        return (
            Source.objects.filter(members__user=self.request.user)
            .annotate(message_count=Count("messages", distinct=True))
            .order_by("title")
        )

    def create(self, request, *args, **kwargs):
        serializer = CreateSourceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        source = services.create_manual_source(request.user, **serializer.validated_data)
        source.message_count = 0
        return Response(SourceSerializer(source).data, status=status.HTTP_201_CREATED)


@extend_schema(tags=["sources"], request=PasteSerializer, responses={201: ImportResultSerializer})
class PasteView(APIView):
    """POST sources/{id}/paste/ — paste messages copied from WhatsApp (or one message)."""

    def post(self, request, source_id):
        source = generics.get_object_or_404(Source, pk=source_id)
        serializer = PasteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return import_result(
            *services.paste_messages(request.user, source, **serializer.validated_data)
        )


@extend_schema(tags=["sources"], request=ExportSerializer, responses={201: ImportResultSerializer})
class ExportView(APIView):
    """POST sources/{id}/export/ — upload WhatsApp's "Export chat" .txt file."""

    parser_classes = [MultiPartParser]

    def post(self, request, source_id):
        source = generics.get_object_or_404(Source, pk=source_id)
        serializer = ExportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        file = serializer.validated_data["file"]
        return import_result(*services.import_whatsapp_export(request.user, source, file))
