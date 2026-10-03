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
| Feed | `GET feed/` (`?tier=`: direct, action, important or digest), `GET feed/{insight_id}/`, `POST feed/{insight_id}/read/`, `POST feed/{insight_id}/dismiss/`, `POST feed/{insight_id}/feedback/` (`not_relevant`) | The caller's own deliveries only, newest first within each tier. The detail includes the summary, structured fields, the **reason** it was shown, and the **evidence** (original message text, sender, group, time, and a link to open the original where the platform has one). Insights not delivered to the caller return **404**. |
| Sources | `GET sources/` (the groups the caller added, with `message_count`), `POST sources/` (`{title, school?, programme?, intake?, course?, section?}`: a group for pasted or uploaded messages; the caller becomes its first member; M4.3), `POST sources/connect/` *[M6]* (`{invite_url, purpose/scope}`: adds the group; UniFlow's number joins it if it isn't connected yet), `DELETE sources/{id}/membership/` (remove the group from my list), `POST sources/{id}/paste/` (`{text, sender_name?}`: text copied from WhatsApp becomes separate messages, anything else one message), `POST sources/{id}/export/` (WhatsApp "Export chat" `.txt`, multipart, 5 MB at most); both answer `{added, already_stored}` | Only academic groups; invite hosts are validated ([08](08-messaging-integrations.md)). |
| Preferences | `GET`/`PATCH users/me/` gains `current_semester` (read-only, worked out from the intake), `semester_override`, `interests`, `info_types`, `aliases`; `GET auth/preferences/choices/` lists the interest and info-type choices as `{value, label}` | Unknown choices → 400; repeats are removed |
| Timetable imports | `POST timetable/imports/` (multipart image, PDF or XLSX, **or** `{link}` for a public Google Drive file), `GET timetable/imports/` (the caller's imports, including ones created from timetables shared in their groups), `GET timetable/imports/{id}/` (the rows the AI read), `PATCH timetable/imports/{id}/` (fix or remove rows), `POST timetable/imports/{id}/confirm/`, `POST timetable/imports/{id}/discard/` | Nothing is saved until confirm. Confirm runs the import service and enrols the caller. |
| Add a class by hand | `POST timetable/sections/` (`{course_code, course_name, section, meetings: [{weekday, start_time, end_time, meeting_type, building, room}]}`) | Creates the course (in the student's school) and the section in the current term if missing, then enrols the caller: **201** when created, **200** when it already existed (its classes are not changed). Students only. |
| Timetable changes | `GET timetable/changes/` (the caller's pending and decided proposals, with evidence), `POST timetable/changes/{id}/confirm/`, `POST timetable/changes/{id}/reject/` | `today/` and `week/` include the caller's **confirmed** changes, and flag pending ones. |
| Timetable | `GET timetable/sections/` (paginated catalogue of the **current term of the caller's calendar**, Foundation or Undergraduate; active sections with their weekly classes), `GET timetable/my-sections/` (my sections this term), `POST timetable/my-sections/` (`{section}`), `DELETE timetable/my-sections/{section_id}/`; `GET timetable/today/` and `GET timetable/week/?date=YYYY-MM-DD` (Monday to Sunday; default this week), both returning `{term, days: [{date, weekday, classes: [{section_id, course_code, course_name, section_code, lecturer_name, start_time, end_time, meeting_type, building, room}]}]}` | The catalogue filters by `course`, `school` and `search`. Only students have sections (others get 403). Only active sections of the current term can be joined (400). No current term → empty catalogue and 400 on changes. "Today" is the Kuala Lumpur date; days outside the current term have no classes. *[M5]* confirmed changes are added. |
| *[Later]* Announcements, documents, events, communities, applications | Browsable lists of each kind | Their information already reaches students through `feed/`. |
| Notifications | `GET notifications/`, `GET notifications/unread-count/`, `POST notifications/{id}/read/`, `POST notifications/read-all/` | Only the caller's own notifications. Each points to a feed item or a timetable change. |
| Home | `GET feed/home/` | `{direct, action, important, todays_classes, pending_timetable_changes, digest_preview, unread_notifications}`, each limited to a few items |
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
| POST | `integrations/telegram/webhook/` | Telegram | Checked with the `X-Telegram-Bot-Api-Secret-Token` header. Stores new group and channel messages. |
| POST | `internal/messages/` | The WhatsApp connector | Signed with `CONNECTOR_SECRET`. Body: `{source_external_id, message_id, sender_ref, sender_name, text, sent_at, reply_to}`. Idempotent per `(source, message_id)`. |
| POST | `internal/sources/joined/` | The WhatsApp connector | Reports that the connector joined a group (its id and title), so the pending `Source` becomes active. |
| GET | `internal/sources/pending/` | The WhatsApp connector | Invite links waiting to be joined. |
| POST | `internal/messages/{id}/files/` | The WhatsApp connector | Uploads an image, PDF or spreadsheet attached to a group message. |

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
