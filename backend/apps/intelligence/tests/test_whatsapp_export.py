from datetime import UTC, datetime

from apps.intelligence.whatsapp_export import looks_like_whatsapp, parse

ANDROID_EXPORT = """﻿01/10/2026, 08:59 - Messages and calls are end-to-end encrypted.
01/10/2026, 09:00 - Ali joined using this group's invite link
01/10/2026, 09:12 - Dr Lee: Tomorrow's CDE2313 class has been moved from 10 AM to 2 PM.
01/10/2026, 09:13 - Sara: Which room?
Is it still B2?
01/10/2026, 09:14 - Ali: <Media omitted>
01/10/2026, 9:20 pm - Dr Lee: Same room: B2
"""

IPHONE_EXPORT = """[01/10/2026, 09:12:33] Dr Lee: Class moved to 2 PM.
[01/10/2026, 9:15:02 PM] Sara: Thanks!
"""

COPIED_IN_APP = """[09:12, 01/10/2026] Dr Lee: Class moved to 2 PM.
[09:13, 01/10/2026] Sara: Thanks"""


def kl(year, month, day, hour, minute, second=0):
    """A Kuala Lumpur time (UTC+8) as UTC, to compare with what parse() returns."""
    return datetime(year, month, day, hour - 8, minute, second, tzinfo=UTC)


def test_android_export_skips_system_lines_and_media_and_joins_lines():
    messages = parse(ANDROID_EXPORT)

    assert [(m.sender_name, m.text) for m in messages] == [
        ("Dr Lee", "Tomorrow's CDE2313 class has been moved from 10 AM to 2 PM."),
        ("Sara", "Which room?\nIs it still B2?"),
        ("Dr Lee", "Same room: B2"),  # only the first ": " separates the sender
    ]
    assert messages[0].sent_at == kl(2026, 10, 1, 9, 12)  # 1 October, Kuala Lumpur time
    assert messages[2].sent_at == kl(2026, 10, 1, 21, 20)  # 9:20 pm


def test_iphone_export_with_seconds_and_narrow_space_before_pm():
    messages = parse(IPHONE_EXPORT)
    assert [m.sender_name for m in messages] == ["Dr Lee", "Sara"]
    assert messages[0].sent_at == kl(2026, 10, 1, 9, 12, 33)
    assert messages[1].sent_at == kl(2026, 10, 1, 21, 15, 2)


def test_messages_copied_in_the_app_have_the_time_first():
    messages = parse(COPIED_IN_APP)
    assert [(m.sender_name, m.text) for m in messages] == [
        ("Dr Lee", "Class moved to 2 PM."),
        ("Sara", "Thanks"),
    ]
    assert messages[0].sent_at == kl(2026, 10, 1, 9, 12)


def test_month_first_dates_are_detected_from_the_file():
    text = "10/25/2026, 09:00 - Ali: hi\n10/02/2026, 09:00 - Ali: earlier"
    messages = parse(text)
    assert messages[0].sent_at == kl(2026, 10, 25, 9, 0)  # 25 October
    assert messages[1].sent_at == kl(2026, 10, 2, 9, 0)  # so this one is 2 October too


def test_an_impossible_date_is_just_text():
    text = "01/10/2026, 09:00 - Ali: The deadline is\n31/02/2026, 09:00 - not a real date"
    assert [m.text for m in parse(text)] == ["The deadline is\n31/02/2026, 09:00 - not a real date"]


def test_plain_text_is_not_whatsapp():
    assert looks_like_whatsapp(COPIED_IN_APP)
    assert not looks_like_whatsapp("Class moved to 2 PM tomorrow.")
    assert parse("Class moved to 2 PM tomorrow.") == []
