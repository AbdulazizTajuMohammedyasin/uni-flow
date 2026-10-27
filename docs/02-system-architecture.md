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
  │ MySQL 8.4│   │ File store: disk │   │ Inngest (events,    │   │ AI provider API  │
  │ (online: │   │ or Supabase      │   │ retries, schedules) │   │ (one module,     │
  │ Postgres)│   │ Storage (online) │   │ calls /api/inngest  │   │  providers.py)   │
  └──────────┘   └──────────────────┘   └─────────────────────┘   └──────────────────┘
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
5. **A modular monolith with few apps.** There is one Django project. A new app is created only when separation is genuinely good practice (like `accounts`); related features share an app. The AI pipeline is one app (`intelligence`), with alerts in `notifications`.
6. **Background work runs on Inngest.** AI calls are slow and can fail, so they never run inside the request that triggered them. The request sends an **event** to Inngest, which calls Django back at `/api/inngest` to run the job, retries it when it fails, and starts the daily jobs on a schedule (see [Background jobs](#background-jobs)). Celery with Redis did this until M9.6m; the developer switched so that online there's no worker or Redis to host.
7. **Connectors are thin and replaceable.** The WhatsApp connector is a separate small process that only forwards messages; the Telegram bot is a webhook. Neither contains any understanding logic. See [08](08-messaging-integrations.md).
8. **The Django admin is the operator's tool in the pilot.** It is used by the developer (super admin) to review new sources, check AI drafts, correct or retract insights, fix timetable data and create official staff posts. React staff pages are built after the pilot. It is mounted at `/django-admin/` so it is not confused with the React `/staff` area.

### Background jobs

- **[Inngest](https://www.inngest.com)** (M9.6j–m; it replaced Celery, Redis and Celery Beat, one group of jobs at a time). Django sends an **event** (e.g. `uniflow/ping`) to Inngest, and Inngest calls Django back at **`/api/inngest`** to run the matching **function**, inside the web service: no worker, no broker. Inngest retries failed functions and starts the daily ones on a schedule (cron). Set up in `config/inngest.py`; locally Inngest's **dev server** (`npx inngest-cli dev`, dashboard on port 8288), online **Inngest Cloud**, whose calls must be signed with `INNGEST_SIGNING_KEY` (unsigned calls get 401). Jobs are plain functions in each app's `functions.py`, registered with `@function(event, retries=…, one_at_a_time_per=…)` or `@function(daily_at="19:00")` (a cron in `TIME_ZONE`) (Inngest's concurrency key: never two runs for the same group at once) and started with `send(event, **data)` after the save commits. "Too many requests" from the AI raises Inngest's `RetryAfterError` (at least 1, 2, 4… minutes). In tests `INNGEST_RUN_NOW` makes `send()` run the jobs at once in the same process, so tests and CI need no Inngest.
- A job saves its own results in the database (for example `Message.triage`); Inngest keeps only the run history shown in its dashboard.
- **Online, both keys are required:** production settings refuse to start without `INNGEST_SIGNING_KEY` and `INNGEST_EVENT_KEY`, naming the missing one.

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
| File type checking | `filetype` (pure Python) | Approved (M4.4) | M4.4 |
| Images | Pillow | Not needed: timetable images are stored with `FileField` and sent to the model as they are | Later, only for resizing |
| Spreadsheets | `openpyxl` | Approved (M5.4): turns each tab of an `.xlsx` timetable into text for the model | M5.4 |
| HTTP requests | `httpx` (already installed with `inngest`) | Approved (M9.15): sends push notifications to the Expo Push API | M9.15 |
| PDF tables | `pdfplumber` (brings `pdfminer.six`, `pypdfium2` and Pillow) | Approved (M9.13): takes the grid out of a PDF timetable as text, so the model puts each class under the right time | M9.13 |
| Static files in production | `whitenoise` | Deferred. Only if the deployment design needs it. | Release milestone |
| AI provider SDK | `google-genai` (Google's official Gemini library) | Approved (M5.1): the developer chose Gemini | M5.1 |
| Background jobs | `inngest` (Inngest's Python library), with Inngest Cloud online and its dev server locally | Approved (M9.6j); replaced `celery` and `redis` (approved before M4.1, removed in M9.6m) | M9.6j |
| WhatsApp connector | **Baileys 7.0.0-rc14** (Node.js 24) | **Approved** in M6.3 (chosen over neonize: more used, fixed faster). Lives in `connectors/whatsapp/`, outside Django. | M6.3 |

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

The rule is simple. **Views never contain visibility or permission logic.** Student views read only the caller's own data (their deliveries, timetable, sources and imports) through selectors, and staff views call `policies.*`. The feed, search and notification code reuse those same functions.

### Two API surfaces from the same apps

| Surface | Prefix | Who uses it | Querysets |
|---|---|---|---|
| Read (student-facing) | `/api/v1/<resource>/` | Everyone who is logged in, and the mobile app later | The caller's own feed (deliveries), timetable, sources and imports |
| Manage (staff dashboard) | `/api/v1/manage/<resource>/` | Users with a matching capability | Everything the user may manage, including drafts and archived items. In the pilot only users and reference data (M2); the rest is done in the Django admin. |

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
    ├── timetable/      [MVP]   CourseSection, ClassMeeting, SectionEnrollment, TimetableImport, ClassChange, confirmations
    ├── intelligence/   [MVP]   sources (groups), SourceMember, Message, MessageFile; Telegram webhook, internal
    │                           endpoint, paste/export, Drive links; providers.py (AI), triage, extraction, timetable
    │                           reading, resolve, merge, Insight (incl. staff posts), Delivery; the student feed and search
    ├── notifications/  [MVP]   Notification, immediate alerts, daily digest  (Device [Later])
    ├── documents/      [Later]
    ├── events/         [Later] browsable event list and calendar
    ├── communities/    [Later] browsable community directory
    └── applications/   [Later] browsable applications directory

connectors/                    # outside backend/ (not Django)
└── whatsapp/           [MVP]   the WhatsApp connector process
```

### Allowed dependencies between apps

An app may only import from the apps listed above it (each line shows what it uses). Cycles are not allowed.

```
core
academics            → core
accounts             → core, academics
timetable            → core, academics, accounts   (audiences imports timetable, so timetable never imports audiences)
audiences            → core, academics, timetable  (courses, sections; [Later] communities)
publishing           → core, academics, accounts, audiences
notifications        → core, accounts
intelligence         → core, academics, accounts, publishing, audiences, timetable, notifications
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
| `DJANGO_CSRF_TRUSTED_ORIGINS` | (none) | Production: UniFlow's own `https://` address, for the Django admin's forms (M9.5) |
| `DJANGO_HSTS_SECONDS` | `3600` | Production: how long browsers remember "HTTPS only"; raise to `31536000` (a year) once HTTPS is confirmed (M9.5) |
| `DJANGO_SECURE_SSL_REDIRECT` | `true` | Production: send `http://` visitors to `https://` (M9.5) |
| `DB_NAME` / `DB_USER` / `DB_PASSWORD` / `DB_HOST` / `DB_PORT` | `uniflow` / `uniflow` / … / `127.0.0.1` / `3306` | Separate variables, so no URL parsing library is needed |
| `CORS_ALLOWED_ORIGINS` | `http://localhost:5173` | The Vite dev server |
| `FRONTEND_DOMAIN` | `localhost:5173` | Becomes Django's `DOMAIN` setting, which Djoser uses to build email links |
| `JWT_ACCESS_MINUTES` / `JWT_REFRESH_DAYS` | `15` / `14` | |
| `ALLOWED_EMAIL_DOMAINS` | `student.aiu.edu.my` | **Decided:** only student addresses can self-register. Staff accounts are created by a super admin (see [06](06-auth-and-permissions.md#registration)). |
| `EMAIL_BACKEND` | `django.core.mail.backends.console.EmailBackend` (dev) | Production uses `anymail.backends.brevo.EmailBackend` (Brevo's HTTPS API; Render's free tier blocks SMTP) with `BREVO_API_KEY`, which production then requires. |
| `DEFAULT_FROM_EMAIL` | `UniFlow <no-reply@…>` | |
| `TIME_ZONE` | `Asia/Kuala_Lumpur` | |
| `MEDIA_ROOT` | `./media` | Local file storage |
| `MAX_UPLOAD_MB` | `10` | Timetable files and uploads |
| `AI_PROVIDER`, `GEMINI_API_KEY`, `AI_FAST_MODEL`, `AI_SMART_MODEL` | `gemini`, *(key)*, `gemini-3.1-flash-lite`, `gemini-3.5-flash` | The AI provider ([12](12-intelligence.md#ai-provider)); tests use `fake` |
| `TELEGRAM_BOT_TOKEN`, `TELEGRAM_WEBHOOK_SECRET` | | The Telegram bot ([08](08-messaging-integrations.md)) |
| `CONNECTOR_SECRET` | | Signs requests from the WhatsApp connector to `/api/v1/internal/` |
| `INNGEST_DEV` | `true` (dev settings), `false` (production) | `true`: Inngest's dev server on this computer; `false`: Inngest Cloud |
| `INNGEST_SIGNING_KEY`, `INNGEST_EVENT_KEY` | | Online only, from Inngest Cloud: the signing key proves each call to `/api/inngest` comes from Inngest; the event key lets Django send events. Never in git. |
| `MESSAGE_RETENTION_DAYS` | `60` | Raw message text is deleted after this ([09](09-security.md)) |
| `S3_BUCKET`, `S3_ENDPOINT_URL`, `S3_REGION`, `S3_ACCESS_KEY_ID`, `S3_SECRET_ACCESS_KEY` | *(empty)* | When set (always online, optional on your laptop; never in tests), uploaded files go to a private **Supabase Storage** bucket (M9.6h) through its S3-compatible connection (`django-storages`). Empty means the disk (`MEDIA_ROOT`). See [10](10-testing-and-deployment.md#uploaded-files-online-supabase-storage-m96h). |

### MySQL configuration (local, native install, no Docker)

- Any local **MySQL 8.x** server works. 8.4 LTS is recommended for staging and production.
- Each developer **creates the `uniflow` database manually**, with `utf8mb4` (the MySQL 8 default). There is no setup script. The account Django uses must be able to create and drop `test_uniflow` for pytest. See [development-setup.md](development-setup.md#1-local-database).
- Django `OPTIONS` sets `{"charset": "utf8mb4", "init_command": "SET sql_mode='STRICT_TRANS_TABLES'"}`.
- `USE_TZ = True`, and every datetime is stored in UTC.
- **Time zone rule.** Code never uses MySQL-side date conversion (the `__date`, `__week_day` or `Trunc*` lookups with a local time zone). Local-day boundaries such as "today in Kuala Lumpur" are computed in Python and then queried as UTC ranges. This means the MySQL time zone tables, which are awkward to load on Windows, are never needed.
- Production settings add `CONN_MAX_AGE = 60`.

## 16. Files

### MVP: timetable files and chat exports

| Aspect | Rule |
|---|---|
| What is stored | `MessageFile` rows: images (PNG, JPG, WEBP), PDFs and spreadsheets (XLSX) from connected groups or uploaded on the Timetable page. Other attachments from groups are ignored. WhatsApp chat exports (`.txt`) are parsed and **not** kept. |
| Checks | Extension **and** real contents (magic bytes, `filetype`); 10 MB per file; chat exports 5 MB |
| Storage | `message_files/{yyyy}/{mm}/{uuid4}.{ext}`: in a private Supabase Storage bucket when `S3_BUCKET` is set (online, and locally if you choose), otherwise on the disk (`MEDIA_ROOT`) (M9.6h); never public; only the student who uploaded it, or the members of the group it came from, can open it through the API |
| Google Drive links | Only `drive.google.com` and `docs.google.com` hosts, public files only, downloaded as PDF or XLSX, same size limit |
| Retention | Deleted with the message text after `MESSAGE_RETENTION_DAYS`; the classes read from them stay |

### Later: documents and posters

| Aspect | Rule | Even later |
|---|---|---|
| Model | Every uploaded file is a `Document` row: library items and attachments go through one model, one set of checks and one download path. Event posters are the exception and are stored directly on `Event`. | |
| Storage | The same as timetable files: Django's storage API, so the disk locally and Supabase Storage online (M9.6h), with no model changes | |
| Paths | `documents/{yyyy}/{mm}/{uuid4}.{ext}` and `posters/{yyyy}/{mm}/{uuid4}.{ext}`. The original filename is stored in a database column and never used as the path. | |
| Allowed types | PDF, DOCX, XLSX, PPTX, PNG, JPG, WEBP. The platform checks both the extension **and** the file's actual contents (magic bytes). | |
| Size limits | 15 MB for documents and 5 MB for images, both configurable | |
| Access | Any logged-in user can download. `GET /api/v1/documents/{id}/download/` streams the file with Django's `FileResponse`. Documents are never served as public media. | Audience checks for documents. `X-Accel-Redirect` or presigned URLs. |
| Posters | Served as public media, with no resizing | Pillow resizing and thumbnails |
| Deletion | Archiving hides the item, and the file is kept | A cleanup command for orphaned files |
