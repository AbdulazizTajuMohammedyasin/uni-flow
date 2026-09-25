# 04 — REST API Design

## Conventions

| Topic | Decision |
|---|---|
| Base path | `/api/v1/`. The version is in the URL. A released mobile app cannot be upgraded instantly, so breaking changes will go to `/api/v2/` while v1 keeps working. Adding fields or endpoints does not need a new version. |
| Two surfaces | **Read:** `/api/v1/<resource>/` serves published, visible content to any logged-in user. **Manage:** `/api/v1/manage/<resource>/` serves the staff dashboard. Every call on the manage surface is checked against the caller's capabilities (see [06](06-auth-and-permissions.md)). |
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

UniFlow registers its own subclass of Djoser's `UserViewSet`, so the paths below are Djoser's. See [06](06-auth-and-permissions.md#djoser-configuration).

| Method | Path | Who | Purpose |
|---|---|---|---|
| POST | `users/` | public | Registration. Takes `{email, full_name, password, re_password}`. The email domain must be in `ALLOWED_EMAIL_DOMAINS`. The new account is inactive and an activation email is sent. |
| POST | `users/activation/` | public | Takes `{uid, token}` |
| POST | `users/resend_activation/` | public | Takes `{email}` |
| GET, PATCH | `users/me/` | auth | Returns the user, role, profile, `profile_complete` and **`capabilities`**. PATCH changes the name, department, programme and intake. The role and email cannot be changed here. |
| POST | `users/set_password/` | auth | Also revokes all of the user's refresh tokens |
| POST | `users/reset_password/` | public | Always returns 204, so it never reveals whether an email is registered |
| POST | `users/reset_password_confirm/` | public | Also revokes all of the user's refresh tokens |
| POST | `jwt/create/` | public | Login. Returns `{access}`, and also `{refresh}` for mobile. The web app gets the refresh token as a cookie instead. Wrong credentials return 401. A correct password on an unactivated account returns 403 `email_not_verified`. A suspended account returns 403 `account_suspended`. |
| POST | `jwt/refresh/` | public | Takes the refresh token from the cookie (web) or the body (mobile). Rotates it. |
| POST | `jwt/verify/` | public | |
| POST | `jwt/logout/` | auth | Blacklists the refresh token and clears the cookie |

These Djoser endpoints are restricted to `super_admin` in the MVP:

- `users/` (GET, the user list)
- `users/{id}/` (the admin detail view)
- **`DELETE users/me/`**, because Djoser's default is a hard delete. Self-service deletion that anonymizes the account comes later.
- `users/set_email/`, `users/reset_email/` and `users/reset_email_confirm/`, because changing an email would bypass the domain check.

## Read surface (student-facing) [MVP]

| Resource | Endpoints | Filters and notes |
|---|---|---|
| Academics | `GET academics/departments/`, `programmes/`, `intakes/`. M7 adds `courses/`, `terms/` and `terms/current/`. | Used for onboarding and filters |
| Announcements | `GET announcements/`, `GET announcements/{id}/` | `category`, `priority`, `publisher_type`, `department`, `pinned`, `date_from`, `date_to`, `search`. Ordered by pinned first, then important first, then `-published_at`. Items the user cannot see return **404**. |
| Documents | `GET documents/`, `GET documents/{id}/`, `GET documents/{id}/download/` | The list shows only items where `listed_in_library` is true. Filters: `category`, `department`, `search`. A download streams the file to any logged-in user. |
| Events | `GET events/`, `GET events/{id}/`, `GET events/calendar/?from=&to=` | `from`, `to`, `category`, `department`, `upcoming=true`. The calendar endpoint returns a lighter shape and allows a range of at most 62 days. |
| Communities | `GET communities/`, `GET communities/{slug}/`, `POST` or `DELETE communities/{slug}/follow/` | `category`, `department`, `programme`, `intake`, `following=true`, `for_me=true` (a simple filter by the user's profile, not a recommendation engine), `search` |
| Timetable | `GET timetable/sections/` (the current term's catalogue), `GET`/`POST timetable/my-sections/`, `DELETE timetable/my-sections/{section_id}/`, `GET timetable/today/`, `GET timetable/week/?date=` | The catalogue filters by `course`, `department` and `search`. Only students can add their own sections. |
| Applications | `GET applications/`, `GET applications/{id}/` | `status` (upcoming, open, closing_soon, closed), `category`, `search`. By default it shows open and closing-soon listings, ordered by `closes_at`. |
| Notifications | `GET notifications/`, `GET notifications/unread-count/`, `POST notifications/{id}/read/`, `POST notifications/read-all/` | Only the caller's own notifications |
| Dashboard | `GET dashboard/` | `{important_announcements, recent_announcements, todays_classes, upcoming_events, closing_applications, recent_documents, followed_communities, unread_notifications}`, each limited to a few items |
| Search | `GET search/?q=` | Needs at least 2 characters. Returns up to 5 results per type, with counts. Matches with `icontains` on title and body. |

## Manage surface (staff dashboard) [MVP]

Every manage endpoint:

- requires the matching capability,
- filters its queryset to what the user may manage (a department staff member sees only their department's items),
- checks the publisher and audience in the request body on the server (for `department_staff`, both must stay inside their own department; see [06](06-auth-and-permissions.md#the-department-boundary-mvp-rule)),
- returns 403 when the capability is missing and 404 for items outside the user's scope.

| Resource | Endpoints | Capability |
|---|---|---|
| Announcements | `manage/announcements/` for list (all statuses) and create, `manage/announcements/{id}/` for GET, PATCH and DELETE (only drafts can be deleted), plus `…/{id}/publish/` and `…/{id}/archive/` | `announcements.manage` |
| Documents | `manage/documents/` for list and multipart upload, `{id}/` for PATCH and DELETE, plus `publish/` and `archive/` | `documents.manage` |
| Events | `manage/events/` for list and create (the poster is multipart), `{id}/`, plus `publish/` and `archive/` | `events.manage` |
| Applications | `manage/applications/` for list and create, `{id}/`, plus `publish/` and `archive/` | `applications.manage` |
| Communities | `manage/communities/` for list and create, `{slug}/` for PATCH and deactivation, and `{slug}/links/` for CRUD | `communities.manage` |
| Timetable | `manage/timetable/terms/` for CRUD (university admin only); `manage/timetable/courses/` for CRUD; `manage/timetable/sections/` for CRUD with nested `meetings/`; `manage/timetable/import/` (POST with `dry_run`) *[with the first adapter]* | `timetable.manage` |
| Users | `manage/users/` for a list filtered by `role`, `department` and `search`, and **POST to create a staff account** (email, full name, role, department; a "set your password" email is sent); `{id}/role/` to PATCH the role and staff department; `{id}/suspension/` to PATCH `is_suspended` | `users.manage` (super admin only) |
| Reference data | `manage/academics/departments/`, `programmes/` and `intakes/` for CRUD | `academics.manage` (university admin and super admin) |

Every manage response includes `can_edit` and `can_publish`, so the dashboard never has to work out permissions itself.

## Integrations [Later]

`POST /api/v1/integrations/telegram/webhook/` checks the secret header. `manage/integrations/inbox/` lets staff review incoming posts and convert them into drafts.

## Example: manage create

`POST /api/v1/manage/announcements/`

```json
{
  "title": "Hostel check-in schedule for new intake",
  "body": "Check-in runs **5–7 October**...",
  "category": "student_affairs",
  "priority": "important",
  "publisher": { "type": "department", "id": 3 },
  "audience": { "departments": [], "programmes": [], "intakes": [12] },
  "attachment_ids": [88],
  "source_platform": "whatsapp",
  "source_url": "https://whatsapp.com/channel/0029Va...",
  "expires_at": "2026-10-08T00:00:00+08:00"
}
```

This creates a **draft**. A follow-up `POST …/{id}/publish/` publishes it immediately and, because the priority is important, notifies the audience.

The read shape at `GET /api/v1/announcements/214/`:

```json
{
  "id": 214,
  "title": "Hostel check-in schedule for new intake",
  "body": "Check-in runs **5–7 October**...",
  "category": "student_affairs",
  "priority": "important",
  "is_pinned": false,
  "publisher": { "type": "department", "id": 3, "name": "Student Affairs" },
  "audience_summary": "Intake Sept 2026",
  "attachments": [{ "id": 88, "title": "Check-in map", "mime_type": "application/pdf", "size_bytes": 482133, "download_url": "https://api.../api/v1/documents/88/download/" }],
  "source": { "platform": "whatsapp", "url": "https://whatsapp.com/channel/0029Va..." },
  "published_at": "2026-09-23T06:00:00Z",
  "expires_at": "2026-10-07T16:00:00Z"
}
```
