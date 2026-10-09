# 04 — REST API Design

## Conventions

| Topic | Decision |
|---|---|
| Base path | `/api/v1/`. The version is in the URL. A released mobile app cannot be upgraded instantly, so breaking changes will go to `/api/v2/` while v1 keeps working. Adding fields or endpoints does not need a new version. |
| Two surfaces | **Read:** `/api/v1/<resource>/` serves the caller's own feed, timetable, sources and imports. **Manage:** `/api/v1/manage/<resource>/` serves the staff dashboard. Every call on the manage surface is checked against the caller's capabilities (see [06](06-auth-and-permissions.md)). |
| Format | JSON in `snake_case`. Datetimes are ISO 8601 in UTC. Class times are local `HH:MM`. |
| Auth | `Authorization: Bearer <access JWT>` on every endpoint except the ones marked *public*. |
| Pagination | Page numbers: `?page=` and `?page_size=` (default 20, maximum 100). *[Later]*: cursor pagination and `?updated_since=` for mobile sync. |
| Filtering | django-filter query parameters. Every list supports `?search=` and `?ordering=`. |
| Errors | Every error has the same shape: `{"error": {"code": "validation_error", "message": "...", "fields": {"title": ["This field is required."]}}}`. `fields` is **always present**: per-field messages for validation errors (a validation error with no field uses `non_field_errors`), and `{}` otherwise. `code` is DRF's error code, for example `not_found`, `permission_denied`, `not_authenticated` or `throttled`. Unknown `/api/v1/` paths return this format too, not HTML. Djoser's errors are wrapped into it as well. |
| Media URLs | Always absolute URLs. |
| Docs | `/api/v1/schema/` (OpenAPI) and `/api/v1/docs/`, in development only |
| Rate limits | Anonymous users 30/min. Login, registration and password reset share an `auth` limit of 10/min per IP. Logged-in users 300/min. |
| Health | `GET /api/v1/health/` is public and returns `{status, db}` |

## Auth — `/api/v1/auth/` (Djoser + SimpleJWT) [MVP]

UniFlow uses **Djoser's own URLs** (`djoser.urls` and `djoser.urls.jwt`), so the paths below are Djoser's standard ones. The one change is that `jwt/create/` and `jwt/refresh/` keep the refresh token in an httpOnly cookie, and `jwt/logout/` deletes it (`apps/accounts/cookie_jwt.py`). See [06](06-auth-and-permissions.md#12-authentication-architecture-mvp).

| Method | Path | Who | Purpose |
|---|---|---|---|
| POST | `users/` | public | Registration. Takes `{email, full_name, password, re_password}`. The email domain must be in `ALLOWED_EMAIL_DOMAINS`. The new account is inactive and an activation email is sent. |
| POST | `users/activation/` | public | Takes `{uid, token}` |
| POST | `users/resend_activation/` | public | Takes `{email}` |
| GET, PATCH | `users/me/` | auth | Returns the user, role, profile, `profile_complete` and **`capabilities`**. PATCH changes the name, school, programme and intake. The role and email cannot be changed here. |
| POST | `users/set_password/` | auth | Change password (M1.7) |
| POST | `users/reset_password/` | public | Always returns 204, so it never reveals whether an email is registered |
| POST | `users/reset_password_confirm/` | public | Set a new password from the reset email (M1.7) |
| POST | `jwt/create/` | public | Login. Takes `{email, password}` and returns `{access}`. The refresh token is set as a secure httpOnly cookie (`uniflow_refresh`, path `/api/v1/auth/jwt/`). Wrong credentials, or an account that isn't activated, return 401. |
| POST | `jwt/refresh/` | public | Reads the refresh-token cookie (or `{refresh}` in the body) and returns a new `{access}`. The cookie is rotated, and the old refresh token stops working. |
| POST | `jwt/logout/` | public | Cancels the refresh token and deletes the cookie |
| POST | `jwt/verify/` | public | |

These Djoser endpoints are restricted to `super_admin` in the MVP:

- `users/` (GET, the user list)
- `users/{id}/` (the admin detail view)
- **`DELETE users/me/`**, because Djoser's default is a hard delete. Self-service deletion that anonymizes the account comes later.
- `users/set_email/`, `users/reset_email/` and `users/reset_email_confirm/`, because changing an email would bypass the domain check.

## Read surface (student-facing) [MVP]

| Resource | Endpoints | Filters and notes |
|---|---|---|
| Academics | `GET academics/schools/`, `programmes/` (`?school=<id>`), `intakes/`. `courses/` (`?school=<id>`, `?search=` on code and name; active courses of active schools), `terms/` (newest first) and `terms/current/` (the term in progress today; during a break the next loaded term, otherwise the one that just ended; 404 if no terms exist) were added in M3.1; both take `?calendar=undergraduate` (default) or `foundation` (M3.4). | Used for onboarding and filters. Returns **active items only**, as a **plain list without pagination**, because the lists are short and dropdowns need every item. Programmes of an inactive school are hidden. A non-numeric `?school=` returns 400. |
| Feed (M7.5) | `GET feed/` (`?tier=`: direct, action, important or digest; paginated; items: `{id, kind, tier, title, summary, importance, relevance, reason, action_required, action_text, starts_at, deadline_at, location, link, not_confirmed, official, read, published_at}`), `GET feed/{insight_id}/`, `POST feed/{insight_id}/read/`, `POST feed/{insight_id}/dismiss/`, `POST feed/{insight_id}/feedback/` (`not_relevant`) | The caller's own deliveries only, newest first within each tier. The detail includes the summary, structured fields, the **reason** it was shown, and the **evidence** (original message text, sender, group, time, and a link to open the original where the platform has one). Insights not delivered to the caller return **404**. Order: direct, action, important, digest, newest first in each. Dismissed and "not relevant" items are hidden from the list (still openable); retracted and expired ones are gone. Read, dismiss and feedback answer **204**. |
| Sources | `GET sources/` (the groups the caller added, with `message_count`), `POST sources/` (`{title, school?, programme?, intake?, course?, section?}`: a group for pasted or uploaded messages; the caller becomes its first member; M4.3), `POST sources/connect/` (M6.4: `{invite_url, title, school?, programme?, intake?, course?, section?}`; only `https://chat.whatsapp.com/<code>` links (look-alike hosts, `http`, and other sites → 400; a Telegram link → 400 explaining how to add the bot); **201** a new `pending` WhatsApp group that UniFlow's number will join, **200** when the same link is already known (the caller is added to its members, it isn't joined twice); a disconnected group → 400), `DELETE sources/{id}/membership/` (remove the group from my list), `POST sources/{id}/paste/` (`{text, sender_name?}`: text copied from WhatsApp becomes separate messages, anything else one message), `POST sources/{id}/export/` (WhatsApp "Export chat" `.txt`, multipart, 5 MB at most); both answer `{added, already_stored}` | Only academic groups; invite hosts are validated ([08](08-messaging-integrations.md)). |
| Preferences | `GET`/`PATCH users/me/` gains `current_semester` (read-only, worked out from the intake), `semester_override`, `interests`, `info_types`, `aliases`; `GET auth/preferences/choices/` lists the interest and info-type choices as `{value, label}` | Unknown choices → 400; repeats are removed |
| Timetable imports | `POST timetable/imports/` (multipart `file`: image, PDF or XLSX, **or** `{link}` for a public Google Drive / Docs file), `GET timetable/imports/` (my latest 10), `GET timetable/imports/{id}/` (`{status, file_name, group, tab, tabs, rows, report, error}`; `group` is the group a shared timetable came from, blank for my own upload (M6.5); poll while `reading`), `PATCH timetable/imports/{id}/` (`{tab}` to show another tab, or `{rows}` to keep only some classes), `POST timetable/imports/{id}/confirm/` (optional `{rows}`), `POST timetable/imports/{id}/discard/` (M5.5) | Nothing is saved until confirm. Confirm runs the import service and enrols the caller. Only the owner can see an import (404 otherwise). A link that only opens with an AIU account is refused with instructions to download it as Excel and upload it. |
| Add a class by hand | `POST timetable/sections/` (`{course_code, course_name, section, meetings: [{weekday, start_time, end_time, meeting_type, building, room}]}`) | Creates the course (in the student's school) and the section in the current term if missing, then enrols the caller: **201** when created, **200** when it already existed (its classes are not changed). Students only. |
| Timetable changes | `GET timetable/changes/` (proposals for the caller's sections from today on: `{id, kind, course_code, course_name, section_code, title, summary, not_confirmed, date, old_start, old_end, old_room, new_date, new_start, new_end, new_room, my_status, evidence: [{quote, group, sender_name, sent_at}]}`; `my_status` is `pending`, `confirmed` or `rejected`), `POST timetable/changes/{id}/confirm/`, `POST timetable/changes/{id}/reject/` (M5.7) | Students only. Answers apply to the caller's own timetable and can be changed. Retracted changes are gone (404). `today/` and `week/` apply the caller's **confirmed** changes (new time or room; a class moved to another day moves; an extra session is added; a cancelled class stays, flagged) and every class has `change: {id, kind, status} or null` (`pending` = not answered yet). |
| Timetable | `GET timetable/sections/` (paginated catalogue of the **current term of the caller's calendar**, Foundation or Undergraduate; active sections with their weekly classes), `GET timetable/my-sections/` (my sections this term), `POST timetable/my-sections/` (`{section}`), `DELETE timetable/my-sections/{section_id}/`; `GET timetable/today/` and `GET timetable/week/?date=YYYY-MM-DD` (Monday to Sunday; default this week), both returning `{term, days: [{date, weekday, classes: [{section_id, course_code, course_name, section_code, lecturer_name, start_time, end_time, meeting_type, building, room}]}]}` | The catalogue filters by `course`, `school` and `search`. Only students have sections (others get 403). Only active sections of the current term can be joined (400). No current term → empty catalogue and 400 on changes. "Today" is the Kuala Lumpur date; days outside the current term have no classes. *[M5]* confirmed changes are added. |
| *[Later]* Announcements, documents, events, communities, applications | Browsable lists of each kind | Their information already reaches students through `feed/`. |
| Notifications (M8.1) | `GET notifications/` (paginated, newest first: `{id, kind, title, body, target_type, target_id, read, created_at}`), `GET notifications/unread-count/` (`{count}`), `POST notifications/{id}/read/` (**204**), `POST notifications/read-all/` (`{marked}`) | Only the caller's own notifications (someone else's → 404). Each points to a feed item or a timetable change (`target_type`, `target_id`). |
| Daily digest (M8.3) | `GET feed/digest/?date=YYYY-MM-DD` (`{date, items}`; without `date`, my latest digest; `date` is null when I have none) | The items included in that day's digest, most important first; same item shape as `feed/` (which now also has `info_type`). |
| Home (M9.1) | `GET feed/home/` | `{direct, action, important, todays_classes, pending_timetable_changes, digest_preview, unread_notifications}`: up to 5 items per level, 3 in the digest preview, 5 changes waiting; same visibility as `feed/`; today's classes include confirmed changes; staff get empty classes and changes. At most 15 database queries. |
| Search | `GET feed/search/?q=` | Searches every insight delivered to the caller (including ones below the display threshold). Needs at least 2 characters. |

## Manage surface (staff dashboard) [MVP]

Every manage endpoint:

- requires the matching capability,
- filters its queryset to what the user may manage (a school staff member sees only their school's items),
- checks the publisher and audience in the request body on the server (for `school_staff`, both must stay inside their own school; see [06](06-auth-and-permissions.md#the-school-boundary-mvp-rule)),
- returns 403 when the capability is missing and 404 for items outside the user's scope.

| Resource | Endpoints | Capability |
|---|---|---|
| Official posts *[after the pilot]* | `manage/insights/` with `origin = staff`: create, PATCH, `{id}/publish/` and `{id}/archive/`. **In the pilot, staff posts are created in the Django admin.** | `announcements.manage` (the name is kept; it means "official posts") |
| Sources *[after the pilot]* | `manage/sources/` for list (filters: platform, status, school), `{id}/` for PATCH (title, scope, trust, status) and `{id}/disconnect/` | `sources.manage` (university admin and super admin; school staff for their own school's sources) |
| Insights *[after the pilot]* | `manage/insights/` for list (filters: kind, source, status, confidence below a value), `{id}/` for GET and PATCH (correct the title, summary, kind, audience or importance), `{id}/retract/` | `insights.review` (school staff for insights from their school's sources; admins for all) |
| AI usage *[after the pilot]* | `manage/intelligence/usage/`: jobs, failures and spend for the current day | `insights.review` (admins) |
| *[Later]* Documents, events, applications, communities | Management of the browsable lists | Their capabilities exist but are unused in the MVP |
| Timetable | `manage/timetable/terms/` for CRUD (university admin only); `manage/timetable/courses/` for CRUD; `manage/timetable/sections/` for CRUD with nested `meetings/`; `manage/timetable/import/` (POST with `dry_run`) *[with the first adapter]* | `timetable.manage` |
| Users | `manage/users/` for a list filtered by `role`, `school` and `search`, and **POST to create a staff account** (email, full name, role, school; a "set your password" email is sent); `{id}/` to GET, or PATCH the name, role, school, job title and `is_suspended` (no deleting; you can't change your own role or suspend yourself) | `users.manage` (super admin only) |
| Reference data | `manage/academics/schools/`, `programmes/` (`?school=`) and `intakes/` for list (including inactive, `?search=`), create, GET and PATCH. **No delete:** PATCH `is_active: false` hides an item from the read lists | `academics.manage` (university admin and super admin) |

Every manage response includes `can_edit` and `can_publish`, so the dashboard never has to work out permissions itself.

## Ingestion [MVP]

| Method | Path | Who | Purpose |
|---|---|---|---|
| POST | `integrations/telegram/webhook/` | Telegram | Checked with the `X-Telegram-Bot-Api-Secret-Token` header (wrong or missing → 403). Stores new group and channel messages once each, and follows the bot being added or removed. Always 200 for a valid secret, so Telegram doesn't resend. Not in the public API docs (M6.1). |
| POST | `internal/messages/` | The WhatsApp connector | Body: `{source_external_id, message_id, sender_ref, sender_name, text, sent_at, reply_to, has_files}`. **201** `{id, created: true}`, or **200** with `created: false` when already stored (idempotent per `(source, message_id)`); **404** if the join wasn't reported. With `has_files`, the AI sorts it after its file arrives. |
| POST | `internal/sources/joined/` | The WhatsApp connector | Body: `{external_id, title, source_id?, notice_sent?}`. The pending `Source` (`source_id`) becomes active; without `source_id` (UniFlow's number added directly) a new active source is created; if the group is already connected, the pending one is merged into it. |
| GET | `internal/sources/pending/` | The WhatsApp connector | `[{id, title, invite_url}]`: WhatsApp groups students added that aren't joined yet. |
| POST | `internal/messages/{id}/files/` | The WhatsApp connector | Multipart `file`: an image, PDF or spreadsheet of that message (`id` from `internal/messages/`), checked by real contents and size. **201** `{id, kind}`. |

**Signing (M6.2):** every `internal/` request has `X-UniFlow-Timestamp` (Unix seconds) and `X-UniFlow-Signature` (hex HMAC-SHA256 of `<timestamp>.<METHOD>.<path>.<raw body>` with `CONNECTOR_SECRET`). Missing, wrong, or more than 5 minutes off → **403**. See `apps/intelligence/connector.py`.

`internal/` endpoints are only reachable from the server itself (nginx does not expose them) and are excluded from the public API docs.

## Example: an official staff post (after the pilot)

`POST /api/v1/manage/insights/` (in the pilot the same fields are filled in the Django admin)

```json
{
  "title": "Hostel check-in schedule for new intake",
  "body": "Check-in runs **5–7 October**...",
  "category": "student_affairs",
  "priority": "important",
  "publisher": { "type": "school", "id": 3 },
  "audience": { "schools": [], "programmes": [], "intakes": [12] },
  "attachment_ids": [88],
  "source_platform": "whatsapp",
  "source_url": "https://whatsapp.com/channel/0029Va...",
  "expires_at": "2026-10-08T00:00:00+08:00"
}
```

This creates a **draft** insight with `origin = staff`. A follow-up `POST …/{id}/publish/` publishes it immediately, and it is delivered and notified like any other insight.

## Example: a feed item

`GET /api/v1/feed/5512/` for a student in CDE2313 Section A:

```json
{
  "id": 5512,
  "kind": "class_moved",
  "tier": "important",
  "title": "CDE2313 class moved to 2 PM tomorrow",
  "summary": "Tomorrow's CDE2313 lecture moves from 10:00 to 14:00.",
  "importance": 80,
  "relevance": 95,
  "reason": "You are in CDE2313 Section A",
  "action_required": false,
  "data": { "course": "CDE2313", "date": "2026-10-02", "old_start": "10:00", "new_start": "14:00" },
  "timetable_change": { "id": 311, "my_status": "pending" },
  "evidence": [
    {
      "source": { "id": 7, "platform": "whatsapp_group", "title": "CDE2313 Sec A" },
      "sender_name": "Dr Lee",
      "sent_at": "2026-10-01T09:12:00Z",
      "quote": "Tomorrow's CDE2313 class has been moved from 10 AM to 2 PM.",
      "open_url": "https://chat.whatsapp.com/…"
    }
  ],
  "created_at": "2026-10-01T09:13:05Z"
}
```

The student confirms with `POST /api/v1/timetable/changes/311/confirm/`.
