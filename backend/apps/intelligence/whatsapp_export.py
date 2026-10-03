"""Read WhatsApp's own text formats into separate messages (no network, no database).

Handles:
- "Export chat" from Android:  01/10/2026, 09:12 - Dr Lee: Tomorrow's class…
- "Export chat" from iPhone:   [01/10/2026, 09:12:33] Dr Lee: Tomorrow's class…
- Messages copied in the app:  [09:12, 01/10/2026] Dr Lee: Tomorrow's class…
Times may be 24-hour or "9:12 am" / "9:12 PM". A line that doesn't start with a date and
time continues the previous message. System lines ("Messages are end-to-end encrypted",
"Ali joined") have no "Sender: " part and are skipped, as are media placeholders.
Dates are day/month unless the file shows they must be month/day (e.g. 10/25/2026).
"""

import re
from dataclasses import dataclass
from datetime import datetime

from django.utils import timezone

DATE = r"\d{1,2}/\d{1,2}/\d{2,4}"
TIME = r"\d{1,2}[:.]\d{2}(?:[:.]\d{2})?(?:[\s  ]?[AaPp]\.?\s?[Mm]\.?)?"

# 01/10/2026, 09:12 - Name: text      [01/10/2026, 09:12:33] Name: text
DATE_FIRST = re.compile(rf"^‎?\[?(?P<date>{DATE}),?\s(?P<time>{TIME})\]?\s(?:-\s)?(?P<rest>.*)$")
# [09:12, 01/10/2026] Name: text
TIME_FIRST = re.compile(rf"^‎?\[(?P<time>{TIME}),\s(?P<date>{DATE})\]\s(?P<rest>.*)$")

MEDIA_PLACEHOLDERS = {
    "<media omitted>",
    "image omitted",
    "video omitted",
    "audio omitted",
    "sticker omitted",
    "gif omitted",
    "document omitted",
    "this message was deleted",
    "you deleted this message",
    "null",
}


@dataclass
class ParsedMessage:
    sent_at: datetime  # timezone-aware (the project's TIME_ZONE)
    sender_name: str
    text: str


def _match(line: str):
    return DATE_FIRST.match(line) or TIME_FIRST.match(line)


def _day_first(dates: list[str]) -> bool:
    """True unless some date can only be month/day (its second number is above 12)."""
    for value in dates:
        first, second = (int(part) for part in value.split("/")[:2])
        if first > 12:
            return True
        if second > 12:
            return False
    return True  # AIU / Malaysia default


def _to_datetime(date_text: str, time_text: str, day_first: bool) -> datetime | None:
    first, second, year = (int(part) for part in date_text.split("/"))
    day, month = (first, second) if day_first else (second, first)
    if year < 100:
        year += 2000
    clean = time_text.replace(" ", " ").replace(" ", " ").replace(".", ":").strip()
    is_pm = clean.lower().replace(" ", "").endswith(("pm", "p:m:"))
    is_am = clean.lower().replace(" ", "").endswith(("am", "a:m:"))
    numbers = re.findall(r"\d+", clean)
    hour, minute = int(numbers[0]), int(numbers[1])
    second_value = int(numbers[2]) if len(numbers) > 2 else 0
    if is_pm and hour < 12:
        hour += 12
    if is_am and hour == 12:
        hour = 0
    try:
        naive = datetime(year, month, day, hour, minute, second_value)
    except ValueError:
        return None  # not a real date: treat the line as ordinary text
    return timezone.make_aware(naive, timezone.get_current_timezone())


def looks_like_whatsapp(text: str) -> bool:
    """True if the text has at least one WhatsApp "date, time … Name: message" line."""
    return any(_match(line) for line in text.splitlines())


def parse(text: str) -> list[ParsedMessage]:
    """Split WhatsApp text into messages, oldest first, as written in the text."""
    lines = text.lstrip("﻿").splitlines()
    matches = [_match(line) for line in lines]
    day_first = _day_first([found["date"] for found in matches if found])

    messages: list[ParsedMessage] = []
    current: ParsedMessage | None = None
    for line, found in zip(lines, matches, strict=True):
        sent_at = _to_datetime(found["date"], found["time"], day_first) if found else None
        if found is None or sent_at is None:
            if current is not None:  # a continuation line of a multi-line message
                current.text += "\n" + line
            continue
        sender, separator, body = found["rest"].partition(": ")
        if not separator:  # a system line such as "Ali joined using this group's invite link"
            current = None
            continue
        current = ParsedMessage(sent_at=sent_at, sender_name=sender.strip(), text=body)
        messages.append(current)

    return [
        message
        for message in messages
        if message.text.strip() and message.text.strip().lower() not in MEDIA_PLACEHOLDERS
    ]
