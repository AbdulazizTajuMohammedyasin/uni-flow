"""Sources API (/api/v1/sources/): my groups, a group for pasted messages, pasting, and
uploading a WhatsApp "Export chat" file. Connecting real groups comes in M6.
Also "Add my timetable" (/api/v1/timetable/imports/): a file or link read by the AI.
"""

from django.db.models import Count
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import generics, status
from rest_framework.parsers import JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from . import files, services, timetable_reading
from .models import Source, TimetableImport
from .serializers import (
    ConfirmImportSerializer,
    CreateSourceSerializer,
    ExportSerializer,
    ImportResultSerializer,
    PasteSerializer,
    SourceSerializer,
    StartImportSerializer,
    TimetableImportSerializer,
    UpdateImportSerializer,
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


# --- Timetable imports: "Add my timetable" ------------------------------------------------


def import_data(timetable_import: TimetableImport) -> dict:
    file = timetable_import.message_file
    return TimetableImportSerializer(
        {
            "id": timetable_import.id,
            "status": timetable_import.status,
            "file_name": file.original_name or "Google Drive file",
            "tab": timetable_import.tab,
            "tabs": timetable_reading.tab_names(timetable_import),
            "rows": timetable_import.rows,
            "report": timetable_import.report,
            "error": timetable_import.error,
            "created_at": timetable_import.created_at,
        }
    ).data


def my_import(request, import_id: int) -> TimetableImport:
    return generics.get_object_or_404(
        TimetableImport.objects.select_related("message_file"), pk=import_id, user=request.user
    )


@extend_schema(tags=["timetable"])
class TimetableImportListView(APIView):
    """GET: my latest timetable imports. POST: start one from a file or a link."""

    parser_classes = [MultiPartParser, JSONParser]

    @extend_schema(responses=TimetableImportSerializer(many=True))
    def get(self, request):
        imports = TimetableImport.objects.filter(user=request.user).select_related("message_file")
        return Response([import_data(item) for item in imports.order_by("-created_at")[:10]])

    @extend_schema(request=StartImportSerializer, responses={201: TimetableImportSerializer})
    def post(self, request):
        serializer = StartImportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if file := serializer.validated_data.get("file"):
            stored = files.save_upload(request.user, file)
        else:
            stored = files.fetch_drive_link(request.user, serializer.validated_data["link"])
        timetable_import = timetable_reading.start_import(request.user, stored)
        return Response(import_data(timetable_import), status=status.HTTP_201_CREATED)


@extend_schema(tags=["timetable"])
class TimetableImportDetailView(APIView):
    """GET: one import (poll it while "reading"). PATCH: another tab, or fewer classes."""

    @extend_schema(responses=TimetableImportSerializer)
    def get(self, request, import_id):
        return Response(import_data(my_import(request, import_id)))

    @extend_schema(request=UpdateImportSerializer, responses=TimetableImportSerializer)
    def patch(self, request, import_id):
        serializer = UpdateImportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        timetable_import = timetable_reading.update_import(
            request.user, my_import(request, import_id), **serializer.validated_data
        )
        return Response(import_data(timetable_import))


@extend_schema(
    tags=["timetable"], request=ConfirmImportSerializer, responses=TimetableImportSerializer
)
class ConfirmImportView(APIView):
    """POST: save the classes and add me to them."""

    def post(self, request, import_id):
        serializer = ConfirmImportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        timetable_import = timetable_reading.confirm_import(
            request.user, my_import(request, import_id), rows=serializer.validated_data.get("rows")
        )
        return Response(import_data(timetable_import))


@extend_schema(tags=["timetable"], request=None, responses=TimetableImportSerializer)
class DiscardImportView(APIView):
    """POST: this isn't my timetable, so nothing is saved."""

    def post(self, request, import_id):
        timetable_import = timetable_reading.discard_import(
            request.user, my_import(request, import_id)
        )
        return Response(import_data(timetable_import))
