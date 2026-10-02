# 02 — System & Backend Architecture

## 5. System architecture

```
 WhatsApp groups        Telegram groups/channels          Staff            Pasted text / chat export
       │                          │                         │                          │
 ┌─────┴──────────────┐   Telegram webhook                  │                          │
 │ WhatsApp connector │           │                         │                          │
 │ (separate process) │           │                         │                          │
 └─────┬──────────────┘           │                         │                          │
       │ signed POST              │                         │                          │
 ┌─────┴──────────────────────────┴─────────────────────────┴──────────────────────────┴────┐
 │  Django + DRF  /api/v1/            sources → intelligence → deliveries → notifications    │
 │  read APIs + /api/v1/manage/ + /api/v1/internal/     permission checks on every call     │
 └──────┬──────────────────┬───────────────────────┬──────────────────────┬─────────────────┘
        │                  │                       │                      │
  ┌─────┴────┐   ┌─────────┴────────┐   ┌──────────┴──────────┐   ┌───────┴──────────┐
  │ MySQL 8.4│   │ Local file store │   │ Job runner          │   │ AI provider API  │
  │ (+ Job   │   │                  │   │ manage.py run_jobs  │──►│ (one module,     │
  │  table)  │   └──────────────────┘   │ (systemd service)   │   │  providers.py)   │
  └──────────┘                          └─────────────────────┘   └──────────────────┘
        ▲
 ┌──────┴─────────────── React web app ───────────────────────┐     Django admin (/django-admin/)
 │  student area (/ …)            staff dashboard (/staff/…)   │     back-office for developers
 └─────────────────────────────────────────────────────────────┘     and super admins only
        [Later] React Native (Expo) app → same /api/v1/
```

These are the key principles:

1. **All business logic lives in the backend.** This covers who can see what, who can manage what, relevance, tiers and every change to data.
2. **The AI reads and proposes; code decides and acts.** Model calls happen in one module (`apps/intelligence/providers.py`). Their output is validated like user input and can only create insights and proposals. See [12](12-intelligence.md).
3. **The frontend is never the security boundary.** The staff dashboard hides actions the user is not allowed to take, but it does this purely for convenience. Every management endpoint enforces the same permission checks, using the same functions (see [06](06-auth-and-permissions.md)).
4. **One API for every client.** The web app, the staff dashboard and the future mobile app all use `/api/v1/` the same way, with login tokens sent as `Authorization: Bearer`. Nothing depends on sessions or server-rendered pages.
5. **A modular monolith.** There is one Django project and one app per feature.
6. **Background work without extra infrastructure.** AI calls are slow and can fail, so they never run inside a web request. They run as rows in a MySQL `Job` table, processed by one long-running management command (see [Background jobs](#background-jobs)). There is still **no Redis, Celery or message broker**.
7. **Connectors are thin and replaceable.** The WhatsApp connector is a separate small process that only forwards messages; the Telegram bot is a webhook. Neither contains any understanding logic. See [08](08-messaging-integrations.md).
8. **Django admin is secondary.** It is enabled for developers and super admins as a back-office tool, to inspect data and fix mistakes. Staff never need it. It is mounted at `/django-admin/` so it is not confused with the React `/staff` area.

### Background jobs

- `core.Job` rows (kind, payload, status, attempts, `run_after`) are created inside the same transaction as the data that needs work (for example, a new `Message` queues a `triage` job).
- `manage.py run_jobs` runs as a systemd service. It claims jobs with `SELECT … FOR UPDATE SKIP LOCKED` (MySQL 8), runs them, and retries failures with a growing delay up to a limit.
- The daily digest and retention clean-up are scheduled by `run_jobs` itself (it queues them once a day), so no separate cron entry is needed.
- In tests, jobs run immediately in the same process.

## 6. Backend architecture

### Libraries

Each library is added **in the task that first needs it**, never earlier.

| Concern | Library | Status | First task |
|---|---|---|---|
| Dependency management | **Pipenv** (`Pipfile` + `Pipfile.lock`), with the virtual environment kept in `backend/.venv` (`PIPENV_VENV_IN_PROJECT=1`) | Decided | M0.4a |
| Framework | Django **5.2 LTS** | Approved | M0.3 |
| API | Django REST Framework | Approved | M0.7 |
| Auth (accounts) | Djoser | Approved | M1.5 |
| Auth (tokens) | djangorestframework-simplejwt, with the blacklist app | Approved | M1.6 |
| MySQL driver | `mysqlclient` (Windows wheels are available) | Approved (part of MySQL) | M0.4 |
| Configuration from `.env` | **No library.** A small `config/env.py` helper (standard library only) reads `backend/.env` if it exists and provides `env_str`, `env_bool` and `env_list`. Real environment variables override the file. | Decided | M0.4 |
| Tests | `pytest`, `pytest-django` | Approved | M0.5 |
| Test data factories | `factory_boy` | Deferred. Plain helper functions until factories are clearly needed. | — |
| Lint and format | `ruff` | Approved | M0.5 |
| CORS for the Vite dev server | `django-cors-headers` | Approved | M0.7 |
| OpenAPI schema | `drf-spectacular` | Approved | M0.7 |
| Filtering | `django-filter` | Approved | M2.2 |
| File type checking | `filetype` (pure Python) | Deferred. Ask for approval when uploads of documents arrive. | Later |
| Images (poster uploads) | Pillow (Django's `ImageField` requires it) | Deferred. Ask for approval when images are stored. | Later |
| Static files in production | `whitenoise` | Deferred. Only if the deployment design needs it. | Release milestone |
| AI provider SDK | `anthropic` (proposed) | **Needs approval** in the first AI task | Intelligence milestone |
| WhatsApp connector | Baileys (Node.js) or neonize/whatsmeow (Python) | **Needs approval** in the connector task. Lives in `connectors/whatsapp/`, outside Django. | Connectors milestone |

### Layering inside each app

```
views.py        HTTP only: parse the request, call selectors and services, return a serializer
serializers.py  input validation and output shape
selectors.py    read queries ("what can this user see?"). Returns QuerySets.
services.py     writes and side effects (create, publish, archive, notify). Uses transactions.
policies.py     permission decisions (can_manage and similar). The API and capabilities both use them.
models.py       data and simple invariants only
admin.py        Django admin registration (back-office)
filters.py      django-filter FilterSets
tests/
```

The rule is simple. **Views never contain visibility or permission logic.** Student views call `selectors.*_visible_to(user)`, and staff views call `policies.*`. The dashboard, search and notification code reuse those same functions.

### Two API surfaces from the same apps

| Surface | Prefix | Who uses it | Querysets |
|---|---|---|---|
| Read (student-facing) | `/api/v1/<resource>/` | Everyone who is logged in, and the mobile app later | Published, visible, unexpired content |
| Manage (staff dashboard) | `/api/v1/manage/<resource>/` | Users with a matching capability | Everything the user may manage, including drafts and archived items |

Each app has both a `views.py` (read) and a `manage_views.py` (manage). Keeping them separate means the read serializers never expose drafts or internal fields, and every manage view carries its permission class.

## 7. Django app structure

```
backend/
├── manage.py
├── Pipfile                     # dependency ranges: [packages] runtime, [dev-packages] test/lint
├── Pipfile.lock                # exact pinned versions + hashes (committed)
├── pyproject.toml              # tool config only: ruff, pytest
├── .env.example
├── .gitignore                  # backend-only ignores
├── config/
│   ├── settings/{base,dev,test,prod}.py
│   ├── urls.py                 # /api/v1/ and /django-admin/
│   ├── api_v1.py               # read routers + manage routers
│   └── wsgi.py / asgi.py
├── core/                       # TimeStampedModel, pagination, error envelope, base permissions, health
└── apps/
    ├── accounts/       [MVP]   User, profiles (incl. preferences), Djoser/JWT wiring, capabilities, staff users
    ├── academics/      [MVP]   School, Programme, Intake; Course, Term
    ├── audiences/      [MVP]   Audience + visibility selectors ("who is affected")
    ├── publishing/     [MVP]   PublishableModel base, publisher policy, publish/archive services
    ├── timetable/      [MVP]   CourseSection, ClassMeeting, SectionEnrollment, ClassChange, confirmations
    ├── sources/        [MVP]   Source, SourceSubscription, Message; Telegram webhook, internal endpoint, paste/export
    ├── intelligence/   [MVP]   providers.py (AI), triage, extraction, resolve, merge, Insight, Delivery
    ├── announcements/  [MVP]   official staff posts (become insights when published)
    ├── notifications/  [MVP]   Notification, immediate alerts, daily digest  (Device [Later])
    ├── feed/           [MVP]   no models — the student's personal feed and search over deliveries
    ├── documents/      [Later]
    ├── events/         [Later] browsable event list and calendar
    ├── communities/    [Later] browsable community directory
    └── applications/   [Later] browsable applications directory

connectors/                    # outside backend/ (not Django)
└── whatsapp/           [MVP]   the WhatsApp connector process
```

### Allowed dependencies between apps

An app may only import from the apps listed below it. Cycles are not allowed.

```
core
academics            → core
accounts             → core, academics
audiences            → core, academics            ([Later] + timetable, communities for extra dimensions)
publishing           → core, academics, accounts, audiences
timetable            → core, academics, accounts
sources              → core, academics, accounts
notifications        → core, accounts
intelligence         → sources, audiences, timetable, notifications
announcements        → publishing, intelligence
feed                 → intelligence, timetable (read selectors only)
```

`intelligence` sits at the top of the pipeline: it calls the services of `timetable` and `notifications`, and those apps never import it. `notifications` stores `target_type` and `target_id` instead of importing content apps.

### Settings and environment variables

The configuration lives in `backend/.env`. That file is ignored by git, and `backend/.env.example` is committed. The dependency-free `config/env.py` loads it, and real environment variables always take precedence.

| Variable | Example | Purpose |
|---|---|---|
| `DJANGO_SETTINGS_MODULE` | `config.settings.dev` | |
| `DJANGO_SECRET_KEY` | *(random 50+ chars)* | |
| `DJANGO_DEBUG` | `true` | |
| `DJANGO_ALLOWED_HOSTS` | `localhost,127.0.0.1` | |
| `DB_NAME` / `DB_USER` / `DB_PASSWORD` / `DB_HOST` / `DB_PORT` | `uniflow` / `uniflow` / … / `127.0.0.1` / `3306` | Separate variables, so no URL parsing library is needed |
| `CORS_ALLOWED_ORIGINS` | `http://localhost:5173` | The Vite dev server |
| `FRONTEND_DOMAIN` | `localhost:5173` | Becomes Django's `DOMAIN` setting, which Djoser uses to build email links |
| `JWT_ACCESS_MINUTES` / `JWT_REFRESH_DAYS` | `15` / `14` | |
| `ALLOWED_EMAIL_DOMAINS` | `student.aiu.edu.my` | **Decided:** only student addresses can self-register. Staff accounts are created by a super admin (see [06](06-auth-and-permissions.md#registration)). |
| `EMAIL_BACKEND` | `django.core.mail.backends.console.EmailBackend` (dev) | Production uses the SMTP backend together with `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` and `EMAIL_USE_TLS`. |
| `DEFAULT_FROM_EMAIL` | `UniFlow <no-reply@…>` | |
| `TIME_ZONE` | `Asia/Kuala_Lumpur` | |
| `MEDIA_ROOT` | `./media` | Local file storage |
| `MAX_UPLOAD_MB` | `15` | |
| `AI_API_KEY`, `AI_TRIAGE_MODEL`, `AI_EXTRACT_MODEL`, `AI_DAILY_SPEND_LIMIT` | | The AI provider ([12](12-intelligence.md#ai-provider)) |
| `TELEGRAM_BOT_TOKEN`, `TELEGRAM_WEBHOOK_SECRET` | | The Telegram bot ([08](08-messaging-integrations.md)) |
| `CONNECTOR_SECRET` | | Signs requests from the WhatsApp connector to `/api/v1/internal/` |
| `MESSAGE_RETENTION_DAYS` | `60` | Raw message text is deleted after this ([09](09-security.md)) |
| *[Later]* `STORAGE_BACKEND`, `AWS_*` | | Not used in the MVP |

### MySQL configuration (local, native install, no Docker)

- Any local **MySQL 8.x** server works. 8.4 LTS is recommended for staging and production.
- Each developer **creates the `uniflow` database manually**, with `utf8mb4` (the MySQL 8 default). There is no setup script. The account Django uses must be able to create and drop `test_uniflow` for pytest. See [development-setup.md](development-setup.md#1-local-database).
- Django `OPTIONS` sets `{"charset": "utf8mb4", "init_command": "SET sql_mode='STRICT_TRANS_TABLES'"}`.
- `USE_TZ = True`, and every datetime is stored in UTC.
- **Time zone rule.** Code never uses MySQL-side date conversion (the `__date`, `__week_day` or `Trunc*` lookups with a local time zone). Local-day boundaries such as "today in Kuala Lumpur" are computed in Python and then queried as UTC ranges. This means the MySQL time zone tables, which are awkward to load on Windows, are never needed.
- Production settings add `CONN_MAX_AGE = 60`.

## 16. File and document strategy [Later]

> In the MVP the only uploaded file is the WhatsApp chat export (`.txt`), which is parsed and not kept. The strategy below applies when documents, posters and message attachments arrive.

| Aspect | MVP | Later |
|---|---|---|
| Model | Every uploaded file is a `Document` row: library items and attachments go through one model, one set of checks and one download path. Event posters are the exception and are stored directly on `Event`. | |
| Storage | Local `MEDIA_ROOT` (`backend/media/`, git-ignored), using Django's storage API | S3-compatible storage through `django-storages`, with no model changes |
| Paths | `documents/{yyyy}/{mm}/{uuid4}.{ext}` and `posters/{yyyy}/{mm}/{uuid4}.{ext}`. The original filename is stored in a database column and never used as the path. | |
| Allowed types | PDF, DOCX, XLSX, PPTX, PNG, JPG, WEBP. The platform checks both the extension **and** the file's actual contents (magic bytes). | |
| Size limits | 15 MB for documents and 5 MB for images, both configurable | |
| Access | Any logged-in user can download. `GET /api/v1/documents/{id}/download/` streams the file with Django's `FileResponse`. Documents are never served as public media. | Audience checks for documents. `X-Accel-Redirect` or presigned URLs. |
| Posters | Served as public media, with no resizing | Pillow resizing and thumbnails |
| Deletion | Archiving hides the item, and the file is kept | A cleanup command for orphaned files |
