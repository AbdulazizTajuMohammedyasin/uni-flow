"""Sources API (/api/v1/sources/): my groups, a group for pasted messages, pasting, and
uploading a WhatsApp "Export chat" file. Connecting real groups comes in M6.
Also "Add my timetable" (/api/v1/timetable/imports/): a file or link read by the AI,
the Telegram bot's webhook (/api/v1/integrations/telegram/webhook/), and the WhatsApp
connector's private addresses (/api/v1/internal/, see connector.py), and the student's
"For you" feed (/api/v1/feed/, see feed.py).
"""

import hmac
import logging
from datetime import date

from django.conf import settings
from django.db.models import Count
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import exceptions, generics, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.parsers import JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from . import connector, feed, files, services, telegram, timetable_reading
from .models import Delivery, Message, Source, TimetableImport
from .serializers import (
    ClaimGroupSerializer,
    ConfirmImportSerializer,
    ConnectorFileSerializer,
    ConnectorMessageSerializer,
    ConnectSourceSerializer,
    CreateSourceSerializer,
    DigestSerializer,
    ExportSerializer,
    FeedbackSerializer,
    FeedDetailSerializer,
    FeedItemSerializer,
    HomeSerializer,
    ImportResultSerializer,
    JoinedSerializer,
    PasteSerializer,
    PendingSourceSerializer,
    SourceSerializer,
    StartImportSerializer,
    TimetableImportSerializer,
    UnclaimedGroupSerializer,
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


@extend_schema(
    tags=["sources"],
    request=ConnectSourceSerializer,
    responses={201: SourceSerializer, 200: SourceSerializer},
)
class ConnectSourceView(APIView):
    """POST sources/connect/ — add a WhatsApp group by its invite link. 201: UniFlow's number
    will join it ("pending"). 200: UniFlow already knows it; you're added to it. Without a link,
    201 with added_by_number: the student adds UniFlow's number to the group."""

    def post(self, request):
        serializer = ConnectSourceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        source, created = services.connect_group(request.user, **serializer.validated_data)
        source.message_count = source.messages.count()
        return Response(
            SourceSerializer(source).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


@extend_schema(tags=["sources"], responses={204: None})
class LeaveSourceView(APIView):
    """DELETE sources/{id}/membership/ — take a group off my list. It stays for the other
    students who added it; when nobody has it any more, UniFlow stops reading it. 404 if it
    isn't in my list."""

    def delete(self, request, source_id):
        source = generics.get_object_or_404(Source, pk=source_id, members__user=request.user)
        services.leave_group(request.user, source)
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(tags=["sources"], responses={200: UnclaimedGroupSerializer(many=True)})
class UnclaimedGroupsView(APIView):
    """GET sources/{id}/unclaimed/ — for my group waiting for UniFlow's number: the groups UniFlow
    joined since, that nobody has claimed (the one I meant, if I typed a different name)."""

    def get(self, request, source_id):
        source = generics.get_object_or_404(Source, pk=source_id)
        groups = services.unclaimed_groups(request.user, source)
        return Response(UnclaimedGroupSerializer(groups, many=True).data)


@extend_schema(tags=["sources"], request=ClaimGroupSerializer, responses={200: SourceSerializer})
class ClaimGroupView(APIView):
    """POST sources/{id}/claim/ — "this joined group is the one I added": my waiting entry is
    merged into it, and the merged group is returned."""

    def post(self, request, source_id):
        source = generics.get_object_or_404(Source, pk=source_id)
        serializer = ClaimGroupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        group = services.claim_group(request.user, source, serializer.validated_data["group"])
        group.message_count = group.messages.count()
        return Response(SourceSerializer(group).data)


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
            "group": file.message.source.title if file.message_id else "",
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
        TimetableImport.objects.select_related("message_file__message__source"),
        pk=import_id,
        user=request.user,
    )


@extend_schema(tags=["timetable"])
class TimetableImportListView(APIView):
    """GET: my latest timetable imports. POST: start one from a file or a link."""

    parser_classes = [MultiPartParser, JSONParser]

    @extend_schema(responses=TimetableImportSerializer(many=True))
    def get(self, request):
        imports = TimetableImport.objects.filter(user=request.user).select_related(
            "message_file__message__source"
        )
        return Response([import_data(item) for item in imports.order_by("-created_at")[:10]])

    @extend_schema(request=StartImportSerializer, responses={201: TimetableImportSerializer})
    def post(self, request):
        serializer = StartImportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if file := serializer.validated_data.get("file"):
            stored = files.save_upload(request.user, file)
        else:
            stored = files.fetch_drive_link(request.user, serializer.validated_data["link"])
        timetable_import = timetable_reading.start_import(
            request.user, stored, serializer.validated_data["semester"]
        )
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


logger = logging.getLogger(__name__)


@extend_schema(exclude=True)  # for Telegram's servers only, not part of the public API
class TelegramWebhookView(APIView):
    """POST integrations/telegram/webhook/ — updates from the UniFlow Telegram bot.

    Telegram sends the secret we gave it (set_telegram_webhook) in a header; anything
    without it is refused with 403. A valid update always gets 200, even one UniFlow
    ignores or can't understand, otherwise Telegram keeps sending it again.
    """

    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = []
    parser_classes = [JSONParser]

    def post(self, request):
        secret = settings.TELEGRAM_WEBHOOK_SECRET
        given = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
        if not secret or not hmac.compare_digest(given.encode(), secret.encode()):
            raise PermissionDenied("Wrong secret.")
        try:
            if isinstance(request.data, dict):
                telegram.handle_update(request.data)
        except (KeyError, TypeError, ValueError):
            logger.exception("Telegram update %s not understood", request.data.get("update_id"))
        return Response({"ok": True})


class ConnectorView(APIView):
    """Base for /api/v1/internal/: only signed requests from the WhatsApp connector."""

    authentication_classes = []
    permission_classes = [connector.ConnectorSignature]
    throttle_classes = []


@extend_schema(exclude=True)
class PendingSourcesView(ConnectorView):
    """GET internal/sources/pending/ — groups to join, from students' invite links."""

    def get(self, request):
        return Response(PendingSourceSerializer(connector.pending_sources(), many=True).data)


@extend_schema(exclude=True)
class JoinedView(ConnectorView):
    """POST internal/sources/joined/ — the connector joined a group; it becomes active."""

    parser_classes = [JSONParser]

    def post(self, request):
        serializer = JoinedSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        source = connector.mark_joined(**serializer.validated_data)
        return Response({"id": source.id, "status": source.status})


@extend_schema(exclude=True)
class ConnectorMessageView(ConnectorView):
    """POST internal/messages/ — a new group message (sending it again changes nothing).
    404 if UniFlow hasn't been told it joined that group (internal/sources/joined/)."""

    parser_classes = [JSONParser]

    def post(self, request):
        serializer = ConnectorMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            message, created = connector.store_message(serializer.validated_data)
        except Source.DoesNotExist:
            raise exceptions.NotFound(
                "UniFlow isn't in this group (report the join first)."
            ) from None
        if message is None:  # the sender asked not to be read: nothing is stored
            return Response({"id": None, "created": False, "skipped": True})
        return Response(
            {"id": message.id, "created": created},
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


@extend_schema(exclude=True)
class ConnectorFileView(ConnectorView):
    """POST internal/messages/{id}/files/ — an image, PDF or Excel file of a message."""

    parser_classes = [MultiPartParser]

    def post(self, request, message_id):
        message = generics.get_object_or_404(
            Message, pk=message_id, source__platform=Source.Platform.WHATSAPP_GROUP
        )
        serializer = ConnectorFileSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        stored = connector.attach_file(message, serializer.validated_data["file"])
        return Response({"id": stored.id, "kind": stored.kind}, status=status.HTTP_201_CREATED)


# --- The "For you" feed -------------------------------------------------------------------


@extend_schema_view(
    get=extend_schema(
        parameters=[
            OpenApiParameter("tier", str, enum=Delivery.Tier.values, description="Only this level.")
        ]
    )
)
@extend_schema(tags=["feed"])
class FeedListView(generics.ListAPIView):
    """GET feed/ - my feed: Direct attention, Action required, Important, then Digest;
    newest first within each. Dismissed and "not relevant" items are hidden."""

    serializer_class = FeedItemSerializer

    def get_queryset(self):
        tier = self.request.query_params.get("tier")
        if tier and tier not in Delivery.Tier.values:
            choices = ", ".join(Delivery.Tier.values)
            raise exceptions.ValidationError({"tier": [f"Use one of: {choices}."]})
        return feed.my_feed(self.request.user, tier)


@extend_schema(tags=["feed"], responses=FeedDetailSerializer)
class FeedDetailView(APIView):
    """GET feed/{insight_id}/ - one of my items, why I see it, and the original messages.
    404 if it was not delivered to me."""

    def get(self, request, insight_id):
        delivery = feed.my_item(request.user, insight_id)
        delivery.evidence = [
            {"message": e.message, "quote": e.quote, "open_url": feed.open_url(e.message)}
            for e in delivery.insight.evidence.all()
        ]
        delivery.timetable_change = feed.my_timetable_change(request.user, delivery)
        return Response(FeedDetailSerializer(delivery).data)


@extend_schema(tags=["feed"], request=None, responses={204: None})
class FeedReadView(APIView):
    """POST feed/{insight_id}/read/"""

    def post(self, request, insight_id):
        feed.mark_read(feed.my_item(request.user, insight_id))
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(tags=["feed"], request=None, responses={204: None})
class FeedDismissView(APIView):
    """POST feed/{insight_id}/dismiss/ - hide it from my feed."""

    def post(self, request, insight_id):
        feed.dismiss(feed.my_item(request.user, insight_id))
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(tags=["feed"], request=FeedbackSerializer, responses={204: None})
class FeedFeedbackView(APIView):
    """POST feed/{insight_id}/feedback/ - {"feedback": "not_relevant"}: hide it, and
    remember it to improve relevance later."""

    def post(self, request, insight_id):
        serializer = FeedbackSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        feed.not_relevant(feed.my_item(request.user, insight_id))
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(
    tags=["feed"],
    responses=DigestSerializer,
    parameters=[
        OpenApiParameter("date", OpenApiTypes.DATE, description="YYYY-MM-DD. Default: my latest.")
    ],
)
class DigestView(APIView):
    """GET feed/digest/?date= - the items of one day's daily digest (the digest alert opens
    this), most important first."""

    def get(self, request):
        raw = request.query_params.get("date")
        try:
            day = date.fromisoformat(raw) if raw else None
        except ValueError:
            raise exceptions.ValidationError({"date": ["Use the format YYYY-MM-DD."]}) from None
        day, items = feed.my_digest(request.user, day)
        return Response(DigestSerializer({"date": day, "items": items}).data)


@extend_schema(tags=["feed"], responses=HomeSerializer)
class HomeView(APIView):
    """GET feed/home/ - the home screen: the first items of Direct attention, Action required
    and Important, today's classes, class changes waiting for me, a digest preview and my
    unread alert count."""

    def get(self, request):
        return Response(HomeSerializer(feed.home(request.user)).data)


@extend_schema(
    tags=["feed"],
    parameters=[OpenApiParameter("q", str, description="Words to look for (2+ characters).")],
)
class SearchView(generics.ListAPIView):
    """GET feed/search/?q= - search everything delivered to me (paginated, newest first)."""

    serializer_class = FeedItemSerializer

    def get_queryset(self):
        text = self.request.query_params.get("q", "").strip()
        if len(text) < feed.MIN_SEARCH:
            raise exceptions.ValidationError({"q": ["Type at least 2 characters."]})
        return feed.search(self.request.user, text)
