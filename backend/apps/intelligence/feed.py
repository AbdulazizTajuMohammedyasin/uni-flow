"""A student's "For you" feed (docs/04-api.md, "Feed"): their own deliveries only.

- my_feed(): what is shown — published, not expired, not dismissed, not marked
  "not relevant"; Direct attention first, then Action required, Important, Digest, newest
  first within each level.
- my_digest(): the items of one day's digest (M8.3).
- my_item(): one item for its detail page (404 if it wasn't delivered to this student).
- open_url(): where "Open original" goes for a message.
- read / dismiss / not relevant: the student's own buttons.
- home(): the home screen in one request (M9.1).
- search(): find my own items by words (M9.2).
"""

from datetime import date, datetime, time, timedelta

from django.db.models import Case, IntegerField, Q, QuerySet, Value, When
from django.shortcuts import get_object_or_404
from django.utils import timezone

from apps.accounts import semesters
from apps.accounts.models import UserRole
from apps.notifications.models import Notification
from apps.publishing.models import Status
from apps.timetable.changes import PENDING, changes_for
from apps.timetable.services import classes_for_days

from .models import Delivery, Message, Source

TIER_ORDER = [
    Delivery.Tier.DIRECT,
    Delivery.Tier.ACTION,
    Delivery.Tier.IMPORTANT,
    Delivery.Tier.DIGEST,
]


def _visible(user) -> QuerySet[Delivery]:
    now = timezone.now()
    return Delivery.objects.filter(
        Q(insight__expires_at__isnull=True) | Q(insight__expires_at__gt=now),
        user=user,
        insight__status=Status.PUBLISHED,  # a retracted item disappears from every feed
    ).select_related("insight")


def my_feed(user, tier: str | None = None) -> QuerySet[Delivery]:
    deliveries = _visible(user).filter(dismissed_at__isnull=True, feedback="")
    if tier:
        deliveries = deliveries.filter(tier=tier)
    rank = Case(
        *[When(tier=value, then=Value(index)) for index, value in enumerate(TIER_ORDER)],
        output_field=IntegerField(),
    )
    return deliveries.annotate(rank=rank).order_by("rank", "-insight__published_at", "-id")


def my_digest(user, day: date | None = None) -> tuple[date | None, QuerySet[Delivery]]:
    """The items of one day's digest (default: my latest digest), most important first."""
    included = _visible(user).filter(
        digested_at__isnull=False, dismissed_at__isnull=True, feedback=""
    )
    if day is None:
        latest = included.order_by("-digested_at").first()
        if latest is None:
            return None, included.none()
        day = timezone.localdate(latest.digested_at)
    start = timezone.make_aware(datetime.combine(day, time.min))
    items = included.filter(digested_at__gte=start, digested_at__lt=start + timedelta(days=1))
    return day, items.order_by("-insight__importance", "-id")


def my_item(user, insight_id: int) -> Delivery:
    """One of my items (dismissed ones too, e.g. from a notification); 404 otherwise."""
    return get_object_or_404(
        _visible(user).prefetch_related("insight__evidence__message__source"),
        insight_id=insight_id,
    )


def open_url(message: Message) -> str:
    """Telegram has a link to each message; WhatsApp only to the group (docs/08)."""
    source = message.source
    if source.platform in (Source.Platform.TELEGRAM_GROUP, Source.Platform.TELEGRAM_CHANNEL):
        username = (message.raw.get("chat") or {}).get("username")
        if username:
            return f"https://t.me/{username}/{message.external_id}"
        if (source.external_id or "").startswith("-100"):  # a private group or channel
            return f"https://t.me/c/{source.external_id[4:]}/{message.external_id}"
        return ""
    if source.platform == Source.Platform.WHATSAPP_GROUP:
        return source.invite_url
    return ""


def my_timetable_change(user, delivery: Delivery) -> dict | None:
    """For a timetable change: the proposal for my section and my answer to it."""
    change = changes_for(user).filter(insight=delivery.insight).first()
    return {"id": change.id, "my_status": change.my_status} if change else None


def mark_read(delivery: Delivery) -> None:
    if delivery.read_at is None:
        delivery.read_at = timezone.now()
        delivery.save(update_fields=["read_at", "updated_at"])


def dismiss(delivery: Delivery) -> None:
    delivery.dismissed_at = delivery.dismissed_at or timezone.now()
    delivery.save(update_fields=["dismissed_at", "updated_at"])


def not_relevant(delivery: Delivery) -> None:
    """The student said it isn't relevant to them: hidden, and remembered for later."""
    delivery.feedback = Delivery.Feedback.NOT_RELEVANT
    delivery.dismissed_at = delivery.dismissed_at or timezone.now()
    delivery.save(update_fields=["feedback", "dismissed_at", "updated_at"])


# --- The home screen (M9.1) ---------------------------------------------------------------

HOME_ITEMS = 5  # per level
DIGEST_PREVIEW = 3


def home(user) -> dict:
    """Everything the home screen shows, in one request: the first few items of the three
    urgent levels, today's classes (with confirmed changes), class changes waiting for an
    answer, a digest preview and the unread alert count. Same visibility as the feed."""
    feed = my_feed(user)
    is_student = user.role == UserRole.STUDENT
    today = semesters.today()
    waiting = (
        changes_for(user)
        .filter(my_status=PENDING)
        .filter(Q(date__gte=today) | Q(new_date__gte=today))
        .prefetch_related("insight__evidence__message__source")
        .order_by("date", "id")[:HOME_ITEMS]
        if is_student
        else []
    )
    return {
        "direct": feed.filter(tier=Delivery.Tier.DIRECT)[:HOME_ITEMS],
        "action": feed.filter(tier=Delivery.Tier.ACTION)[:HOME_ITEMS],
        "important": feed.filter(tier=Delivery.Tier.IMPORTANT)[:HOME_ITEMS],
        "digest_preview": feed.filter(tier=Delivery.Tier.DIGEST)[:DIGEST_PREVIEW],
        "todays_classes": classes_for_days(user, [today])["days"][0]["classes"]
        if is_student
        else [],
        "pending_timetable_changes": waiting,
        "unread_notifications": Notification.objects.filter(
            recipient=user, read_at__isnull=True
        ).count(),
    }


# --- Search (M9.2) --------------------------------------------------------------------------

MIN_SEARCH = 2  # characters


def search(user, text: str) -> QuerySet[Delivery]:
    """My items (read, dismissed and digested ones too) containing every word of `text` in
    the title, summary, place, "what to do" or a quoted original message; newest first.
    Only ever my own deliveries: nothing delivered to someone else."""
    results = _visible(user)
    for word in text.split()[:10]:
        results = results.filter(
            Q(insight__title__icontains=word)
            | Q(insight__summary__icontains=word)
            | Q(insight__location__icontains=word)
            | Q(insight__action_text__icontains=word)
            | Q(insight__evidence__quote__icontains=word)
        )
    return results.distinct().order_by("-insight__published_at", "-id")
