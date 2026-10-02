# 07 — Notification Architecture

Notifications follow the priority tiers from [01](01-product.md#priority-tiers). The goal is the opposite of a WhatsApp group: **interrupt only when it really matters to this student**.

## MVP: in-app notifications from deliveries

In the MVP, alerts appear **inside UniFlow only** (the bell and the notifications page). A student who is not using UniFlow sees them the next time they open it. Phone push notifications arrive with the mobile app (Later).

```
intelligence: Delivery rows created for an insight (one per affected student, with a tier)
        │  same transaction → Job "notify" for that insight
        ▼
notifications.services.notify_deliveries(insight)
        │  immediate tiers: direct / action / important  → Notification now
        │  digest tier: nothing now; picked up by the daily digest
        │  claim: Delivery.notified_at set once, so an insight never notifies twice
        ▼
Notification.objects.bulk_create(batch_size=1000, ignore_conflicts=True)   ← unique(recipient, dedupe_key)
        ▼
web client polls GET /notifications/unread-count/ every 60 s (tab visible) → bell badge
```

| Trigger | Kind | Who | When | Dedupe key |
|---|---|---|---|---|
| A student is mentioned by name | `direct_attention` | That student | Immediately | `ins:{id}:u:{user}` |
| Action-required insight, relevant to the student | `action_required` | Delivered students in the `action` tier | Immediately | `ins:{id}:u:{user}` |
| Important insight (importance ≥ 70), relevant to the student | `important_update` | Delivered students in the `important` tier | Immediately | `ins:{id}:u:{user}` |
| A timetable change is proposed for the student's section | `timetable_change_proposed` | Students with a pending confirmation | Immediately | `chg:{id}:u:{user}` |
| A proposed or confirmed change is retracted | `timetable_change_retracted` | Students who had it pending or confirmed | Immediately | `chg:{id}:retract:u:{user}` |
| Daily digest | `digest` | Students with undigested digest-tier deliveries | Once a day (default 19:00 Kuala Lumpur time) | `dig:{date}:u:{user}` |
| Admin broadcast | `system` | Everyone | Immediately | `sys:{id}` |

- **Merged duplicates don't notify again.** When a forwarded copy is merged into an existing insight ([12](12-intelligence.md#5-merge-duplicates)), no new notification is sent.
- **Every notification opens the insight**, and from there the original message.
- The digest is one notification that opens a digest page listing the day's digest-tier insights, grouped by information type.
- Notifications are created by `run_jobs` ([02](02-system-architecture.md#background-jobs)), never inside a web request. For about 10k students, `bulk_create` in batches finishes in well under a second.

## Later

| Feature | Needs |
|---|---|
| Push notifications (React Native app): the main way to reach students outside UniFlow | A `Device` model, `POST /notifications/devices/`, and a push channel using the Expo Push API, run from `run_jobs` with retries |
| Email digest | The SMTP settings (M10 release) and a per-user choice |
| Per-tier preferences and quiet hours | A `NotificationPreference` model |
| Deadline reminders ("internship closes tomorrow") | A reminder job for action-required insights with `deadline_at` |
| Retention | A monthly job that prunes read notifications older than 180 days |

`notify_deliveries(insight)` stays the one entry point, so none of these additions change the code that calls it.
