# 07 — Notification Architecture

Notifications follow the priority tiers from [01](01-product.md#priority-tiers). The goal is the opposite of a WhatsApp group: **interrupt only when it really matters to this student**.

## MVP: in-app notifications from deliveries

In the MVP, alerts appear **inside UniFlow only** (the bell and the notifications page). A student who is not using UniFlow sees them the next time they open it. Phone push notifications arrive with the mobile app (Later).

```
intelligence: Delivery rows created for an insight (one per affected student, with a tier)
        │  after the transaction commits → Inngest job "notify-insight" for that insight
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
- Notifications are created by a background job (Inngest since M9.6k, [02](02-system-architecture.md#background-jobs)), never inside a web request. For about 10k students, `bulk_create` in batches finishes in well under a second. The daily digest is started by Inngest's schedule.

## Later

| Feature | Needs |
|---|---|
| Push notifications (React Native app): the main way to reach students outside UniFlow | Built (M9.14 to M9.16, below). Pushes start once `EXPO_ACCESS_TOKEN` is set on Render |
| Email digest | A per-user choice (email sending itself works through Brevo since M9.8) |
| Per-tier preferences and quiet hours | A `NotificationPreference` model |
| Deadline reminders ("internship closes tomorrow") | A reminder job for action-required insights with `deadline_at` |
| Retention | A monthly job that prunes read notifications older than 180 days |

`notify_deliveries(insight)` stays the one entry point, so none of these additions change the code that calls it.

## Built (M9.14): phones and push settings

The first part of push notifications for the mobile app. Nothing is sent to phones yet.

- **Registering a phone.** The website runs inside the app, which hands it the phone's Expo push address (not a credential). The website sends it with its normal login: `POST notifications/devices/`. The user always comes from the login, never from the request.
- **One phone, one owner.** A push address is unique. When another student logs in on the same phone, it moves to them, so they never get the previous student's alerts. A student can have several phones.
- **Logging out** calls `POST notifications/devices/unregister/` first, which switches the phone off (reason `logout`). It answers 204 even for an address that isn't the caller's, so nothing is revealed.
- **Only students** register phones and have push settings; staff get 403. Suspended or deactivated accounts are already refused at login.
- **Push settings** (`notifications/push-settings/`): three switches for the phone (class changes; when something needs you; the daily digest). All on until the student changes one. They don't affect the bell.
- Registration is throttled at 30 calls an hour per user (scope `devices`), since the website registers on every page load in the app.
- The Django admin lists phones and settings (read-only), without the push address.

## Built (M9.15): sending pushes

Every alert UniFlow already sends (a `Notification` row: targeted, published insights only, never twice) is also pushed to its recipient's phones. Nothing about who gets what is decided again, so a push never reaches someone the bell wouldn't. Code: `apps/notifications/push.py`, jobs in `apps/notifications/functions.py`.

```
notifications.send() → rows saved → "uniflow/notifications.created"
   └─► push-notifications (one run at a time; also every 5 minutes, in case an event was missed)
         1. claim new rows once (Notification.pushed_at; locked rows are skipped)
         2. one PushTicket per row and phone → Expo Push API, 100 per request
   └─► check-push-receipts (every 15 minutes): what Google or Apple said
```

| Rule | Why |
|---|---|
| A row is claimed once (`pushed_at`), and the migration marks every existing row as claimed | Nothing is pushed twice, and turning push on never sends a backlog |
| Not pushed: rows older than 1 hour, recipients who are inactive or suspended, kinds switched off in push settings (`system` alerts always go) | A delayed job must not wake people with stale alerts; they're still in the bell |
| Only phones registered before the alert; a phone that moves to another student counts as new | A newly installed or handed-on phone doesn't get older alerts |
| Expo unreachable, HTTP 429 or 5xx: tickets stay pending and the job tries again after 1, 2, 4… minutes (5 tries); pending tickets older than 1 hour are given up | No lost pushes during a short outage, no stale ones after a long one |
| Any other HTTP 4xx is a mistake in the request: logged, tickets marked as errors, no retry | Trying again wouldn't help |
| `DeviceNotRegistered` (in Expo's answer or a later receipt) switches the phone off | The app was removed or notifications were turned off |
| `InvalidCredentials` / `MismatchSenderId` in a receipt are logged as errors | The Firebase or Apple set-up in Expo is wrong |
| A phone not used for 14 days (the login's lifetime) is switched off daily at 03:00 (`deactivate-stale-devices`) | The session there has ended; this stops alerts to a phone whose student never logged out |
| Tickets are deleted after 7 days | They're only needed for receipts and troubleshooting |
| Logs hold ticket ids, device ids, counts and error codes only | Never a push address, the access token or the alert's text |

The message: the alert's `title` and `body`; `data` = `{v: 1, notification_id, target_type, target_id}` (the app works out the page itself, so there's never a link); Android `channelId` and `priority` by kind (`class-changes` and `needs-you`: high; `digest` and `general`: normal); and the iPhone `badge` = the recipient's unread count, the same number as the bell.

Without `EXPO_ACCESS_TOKEN` the push job does nothing (development); rows wait unclaimed and are pushed, if still under an hour old, once the token is set.

## Built (M9.16): the website inside the phone app

The UniFlow app shows this website in a WebView and announces itself with `window.UniFlowApp` (platform, app version, the phone's push address). The website holds the login, so it registers the phone; the app never sees a login token. Code: `frontend/src/lib/app.ts` and `usePhoneRegistration` in `AuthContext.tsx`. In an ordinary browser none of this runs.

| When | What the website does |
|---|---|
| A student is logged in (login, or a session restored on load) and the app has a push address | `POST notifications/devices/`, at most once per address per page load, then tells the app `push-registration: registered` (or `failed`) |
| The app announces an address later (`uniflow:push-token` event, e.g. after notifications are allowed, or on a page restored by Back) | Registers it the same way; `null` means notifications are off, so nothing happens |
| Logout | `POST notifications/devices/unregister/` **before** logging out (errors are ignored and never block logging out), then tells the app `push-registration: unregistered` |
| Someone logs in or out | Tells the app `session: {signedIn}` |
| The unread count changes | Tells the app `unread: {count}`, so the app icon matches the bell (the badge keeps its `"{count} unread"` label too) |

Messages to the app are JSON with `"v": 1`, sent with `window.ReactNativeWebView.postMessage`; they never carry login tokens or personal data. Staff never register a phone.

**Profile → Phone notifications** (students, inside the app only): three switches bound to `notifications/push-settings/` (Class changes; When something needs you; Daily digest). Each saves at once.

## Built (M8.2)

- `notify_deliveries(insight)` lives in `apps/intelligence/delivery.py` (not in `notifications`), so the `notifications` app never depends on `intelligence` (see [02](02-system-architecture.md)). The `notifications` app only provides `services.send(alerts)`, which any part of UniFlow can use.
- It runs as an Inngest function (`notify_insight`, event `uniflow/insight.delivered`; M9.6k, before that a Celery job) after the save commits, never retried so no one is alerted twice: when an insight is published, and when names in it are matched. Each delivery is claimed with `notified_at`, and every alert has a `dedupe_key` (`ins:{insight}:u:{user}`), so nothing is sent twice even if a job runs again.
- A timetable change for the student's own section is sent as `timetable_change_proposed`; other Important deliveries as `important_update`.
- Merged copies: the copy's group members get the insight in their feed, but their new deliveries are marked as already notified (no alert).
- Retraction (`notify_retraction`, Inngest event `uniflow/insight.retracted`): students who were alerted about a timetable change get `timetable_change_retracted` (`ins:{insight}:retract:u:{user}`).

## Built (M8.3): the daily digest

- Inngest runs `send_daily_digest` every day at **19:00** Kuala Lumpur time (`@function(daily_at="19:00")` in `intelligence/functions.py`, next to the 03:00 clean-up; M9.6l, before that Celery Beat). It is never retried, so no one gets two digests.
- `send_daily_digests()` (in `intelligence/delivery.py`) collects each student's Digest-tier deliveries not yet in a digest (`digested_at` empty), leaving out dismissed, "not relevant", retracted and expired ones. Students with **nothing new get nothing**.
- Each other student gets **one** `digest` notification: "Your daily digest: N new items", the top 3 titles by importance as the body, `target_type = "digest"`, `target_id` = the date as a number (e.g. `20261009`), and dedupe key `dig:{date}:u:{user}`, so **at most one per day** even if the job runs twice. The items are then marked `digested_at`.
- The digest page (`/digest?date=YYYY-MM-DD`, API `GET feed/digest/?date=`; without a date, the latest digest) lists that day's items grouped by information type, each linking to its item page. Digest items also stay in the Digest section of For you.
