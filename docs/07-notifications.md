# 07 — Notification Architecture

## MVP: in-app notifications, created when content is published

```
staff: POST /manage/announcements/{id}/publish/      (or events)
        │ publishing.services.publish(obj)  → status=published, published_at=now
        │ transaction.on_commit
        ▼
notifications.services.notify_audience(kind, obj)
        │ claim: UPDATE … SET notified_at=now WHERE id=? AND notified_at IS NULL  (only once per item)
        │ recipients = audiences.selectors.students_matching(obj.audience)
        ▼
Notification.objects.bulk_create(batch_size=1000, ignore_conflicts=True)   ← unique(recipient, dedupe_key)
        ▼
web client polls GET /notifications/unread-count/ every 60 s (tab visible) → bell badge
```

| Trigger | Kind | Who is notified | Dedupe key |
|---|---|---|---|
| An announcement with `important` priority is published | `announcement_important` | The audience | `ann:{id}:pub` |
| An announcement with `normal` priority is published | *No notification* | – | – |
| An event is published | `event_new` | The audience | `evt:{id}:pub` |
| An admin sends a broadcast (super admin) | `system` | Everyone | `sys:{id}` |

**Normal announcements do not notify anyone.** Students are leaving WhatsApp because of noise, so only important items interrupt them.

There is **no cron, queue or reminder system** in the MVP. For about 10k students, `bulk_create` in batches finishes within the request in well under a second.

## Later

| Feature | Needs |
|---|---|
| "Application closing soon" reminders, application opened, scheduled publishing | A cron-driven management command, `run_scheduled_jobs`, protected by a MySQL `GET_LOCK` |
| `event_updated` and `timetable_changed` | The update services compare meaningful fields (time, location, room) before and after an edit and notify only when those change |
| `document_new` | The document audience feature |
| Push notifications (React Native) | A `Device` model, `POST /notifications/devices/`, and a `PushChannel` using the Expo Push API. A queue becomes worth adding at this point because push needs retries and delivery receipts. |
| Email digest and per-type preferences | A `NotificationPreference` model |
| Retention | A monthly command that prunes read notifications older than 180 days |

`notify_audience(kind, obj)` stays the one entry point, so none of these additions change the code that calls it.
