# UniFlow Documentation

Status: **M0–M2 are built.** After M2.8 the product was **redefined as an AI-powered student information assistant** ([01](01-product.md)), and the architecture and roadmap were re-planned around it. The next task is M3.1.

Throughout these docs, **[MVP]** means the item is built in milestones M0–M10. **[Later]** means it is designed and documented but not built yet.

> **Want the simple version?** [PROGRESS.md](PROGRESS.md) shows, in plain words, what is done, what is next, and where each file is.

## Reading order

| # | Document | Covers |
|---|---|---|
| 01 | [Product definition](01-product.md) | What UniFlow is (an AI information assistant), relevance vs importance, tiers, timetable intelligence, sources, scope, roles |
| 02 | [System & backend architecture](02-system-architecture.md) | System architecture, the read and manage API surfaces, Django apps, libraries, environment, MySQL, files |
| 03 | [Data model](03-data-model.md) | Entities, constraints, audience targeting, the timetable data flow |
| 04 | [REST API](04-api.md) | Auth (Djoser and SimpleJWT), the read surface, the manage surface |
| 05 | [Frontend](05-frontend.md) | The React student area, the staff dashboard, and future React Native |
| 06 | [Auth & permissions](06-auth-and-permissions.md) | Djoser configuration, JWT, how roles map to capabilities and scope |
| 07 | [Notifications](07-notifications.md) | Immediate alerts by tier, timetable-change alerts, the daily digest |
| 08 | [Sources & connectors](08-messaging-integrations.md) | WhatsApp connector (and its risks), Telegram bot, staff posts, paste and chat export, connecting a group |
| 09 | [Security](09-security.md) | Threats and controls |
| 10 | [Testing & deployment](10-testing-and-deployment.md) | Test layers, CI, deployment without Docker |
| 11 | [Roadmap](11-roadmap.md) | **The development workflow**, milestones M0–M10, task cards, the Later backlog |
| 12 | [Intelligence pipeline](12-intelligence.md) | How messages become insights: triage, understanding, resolving, merging, relevance and tiers, mentions, the AI provider, evaluation and cost |

## Repository structure and where configuration lives

```
UniFlow/
├── .gitattributes        # repo-wide: line endings
├── .editorconfig         # repo-wide: indentation/charset
├── .gitignore            # repo-wide: OS/editor files ONLY
├── .github/workflows/    # repo-level CI (backend.yml, frontend.yml)
├── README.md
├── docs/
├── backend/              # Django API — owns its own .gitignore, .env.example, Pipfile, Pipfile.lock, pyproject.toml
├── connectors/whatsapp/  # the WhatsApp connector process (added in M6)
└── frontend/             # React app — owns its own .gitignore, .env.example, package.json, oxlint/tsconfig/vite config
```

- Settings that apply to only one side of the project live inside `backend/` or `frontend/`.
- **Docker images only for running the backend online** (`backend/Dockerfile`, `connectors/whatsapp/Dockerfile`, and `deploy/` to try them locally, M9.6); development stays native. The website has no Docker image (Vercel builds it). No `mobile/` or `packages/` folders until the React Native work is approved.

## Key architecture decisions

| # | Decision |
|---|---|
| D1 | A modular Django monolith with **few apps**: a new app only when separation is genuinely good practice. Each app is split into selectors (reads), services (writes) and policies (permissions). The AI pipeline (groups, messages, insights, feed) is one app, `intelligence`; alerts are `notifications`. |
| D2 | One versioned API at `/api/v1/` for web now and mobile later. It has two surfaces: **read** (`/api/v1/<resource>/`) and **manage** (`/api/v1/manage/<resource>/`). |
| D3 | **In the pilot, the Django admin (`/django-admin/`) is the operator's tool** for sources, AI drafts, corrections, timetable data and official posts. React staff pages (`/staff`) are built after the pilot (M10). |
| D4 | **The frontend is not a security boundary.** Roles map to *capabilities*, and a school scope limits what each user can manage. The same functions drive both the API's permission checks and the `me.capabilities` field that the UI uses to hide actions. |
| D5 | Official staff posts are **insights with `origin = staff`**: one table and one lifecycle for everything students receive. There is no separate announcements table. Publishers are `university_admin` (any school, any audience) and `school_staff` (only their own school). Lecturers are read-only. |
| D6 | A single `Audience` model per insight or post is the **hard filter** of who can receive it: schools, programmes, intakes, and (from M3) courses and sections. Relevance is then scored per student. |
| D7 | Background work (AI calls, notifications, digest, retention) runs in **Celery with Redis** as the broker; daily jobs use Celery Beat. Redis runs in WSL during development; tests need no Redis. Online, the backend runs on Render (D23). |
| D8 | **Djoser's own URLs** (`djoser.urls` and `djoser.urls.jwt`) handle accounts and login, and SimpleJWT handles tokens. There are no custom login views. Tokens are returned as `{access, refresh}` for web and mobile alike. `is_active` means the email is verified. |
| D9 | Documents, events, applications and communities as browsable lists are **[Later]**. Their information reaches students as insights. |
| D10 | The timetable is the **student's current reality**. The normal timetable is **read by the AI** from timetables shared in groups or uploaded by students (images, PDFs, spreadsheets, Google Drive links), and changes are detected in messages. **Nothing is saved until the student confirms.** Students can also add a class by hand. |
| D11 | Messaging platforms are **primary sources**. Telegram uses the official bot. **WhatsApp uses an unofficial connector, chosen knowingly** with the risks and safeguards in [08](08-messaging-integrations.md). Manual paste and chat export always work as a fallback. |
| D12 | Native MySQL 8.4 for development; **PostgreSQL in production** (Render, D23). Local-day logic (such as "today in Kuala Lumpur") is computed in Python, so MySQL's time zone tables are never needed. |
| D13 | Libraries are added only in the task that needs them, and only once approved. |
| D14 | **shadcn/ui** (Radix-based, preset "nova") provides the UI components, themed with UniFlow indigo as the primary colour. Components live in `src/components/ui/` and UniFlow's own small components live in `src/shared/ui/`. |
| D15 | **The AI reads and proposes; code decides and acts.** All model calls go through `intelligence/providers.py`; output is schema-validated; relevance and tiers are computed by code per student. |
| D16 | **Relevance and importance are separate.** Importance per insight (AI), relevance per student (code); four tiers: direct attention, action required, important update, digest. |
| D17 | **Every insight links to its source** (evidence messages with sender, group and time). |
| D18 | Academic information only. Raw message text and files are deleted after `MESSAGE_RETENTION_DAYS`; personal chats are never read. |
| D19 | **How sure the AI must be:** sure (≥ 0.8) → shown; unsure (0.5–0.8) → daily digest marked "Not confirmed"; very unsure (< 0.5) → hidden until checked. |
| D20 | **Alerts stay inside UniFlow** in the MVP. Phone notifications arrive with the mobile app. |
| D21 | **Students add their groups in the app** and UniFlow's own number joins them. The students who added a group (`SourceMember`) are the main signal for who a message affects and who is mentioned. Students never give their phone number; the student email is the only verification. |
| D22 | **Pilot first:** one intake and a handful of real groups, operated through the Django admin, before staff pages and a wider release. |

## Remaining decisions

1. **Gemini free tier vs paid tier** (privacy: on the free tier Google may use what is sent). The developer chose the free tier for now; decide before real students' messages are processed (**M9.7**).
2. **WhatsApp connector library** (Baileys or neonize/whatsmeow) and a **dedicated WhatsApp number**. Needed before **M6.3**.
3. **University approval** for reading academic groups. Needed before the pilot (**M9.7**).
4. The university's own timetable export (for an extra import adapter). Not blocking: the AI reads shared timetables.
5. Hosting. Needed before **M9.6**. It must keep the WhatsApp connector online.
6. Libraries decided when their task arrives: `filetype` (M4.4), `openpyxl` (M5.4, only for spreadsheets), `factory_boy`, `openapi-typescript`, `whitenoise`.

### Resolved

- **Product direction (after M2.8):** UniFlow is an AI-powered student information assistant, not a staff notice board. The WhatsApp connector is unofficial by the developer's choice. Staff posts stay as one official source. M2 code is kept. The roadmap proves an AI timetable slice before building the full feed.
- **Re-evaluation (after the redefinition):** staff posts and AI findings are one model; the AI reads normal timetables from shared files and links; the confidence rule (D19); alerts inside UniFlow until the mobile app (D20); students add groups and UniFlow's number joins them, no phone numbers (D21); pilot first with the Django admin (D22).

- **Supporting libraries:** approved are `pytest`, `pytest-django`, `ruff`, `django-cors-headers`, `drf-spectacular`, `django-filter`, Vitest and React Testing Library. `django-environ` is rejected in favour of a small `config/env.py` helper that uses only the standard library.
- **Registration:** only `@student.aiu.edu.my` addresses can self-register. Staff accounts are created by a super admin (M2.2), or in the Django admin until then.
- **Terminology:** AIU is organised into **Schools** (plus the Centre for Foundation and General Studies, stored as a School). A Programme is the degree and belongs to one school. A Course is a subject or module (for example CDE2313). UniFlow therefore uses "school" everywhere: the role is `school_staff`, and staff manage content for their own school.
- **School staff** manage only content that belongs to and is targeted within their own school.
- **CI:** a MySQL service container in GitHub Actions is acceptable. Local development has no Docker.
- **D23 (M9.6, M9.6b): hosting.** The **backend runs on Render** from Docker images (Django on gunicorn as a web service; the Celery worker, Celery Beat and the WhatsApp connector as background workers), the **website on Vercel** (built from `frontend/`, no Docker), and the **production database is PostgreSQL** (Render has no MySQL; development stays on MySQL; CI tests both). The free Vercel and Render addresses are used, so **Vercel forwards `/api/` to Render** and the browser sees one site, which keeps the login cookie working in every browser. Approved: gunicorn, whitenoise, psycopg. A single-server setup with Caddy was written first and dropped before committing.
- **D24 (M9.6j–l): background jobs move from Celery to Inngest.** Inngest calls the web service at `/api/inngest` to run each job, so online there is no worker, no Beat and no Redis to host or pay for, and its dashboard shows every run. Moved one group of jobs at a time (set-up, AI and alerts, files and daily jobs, then Celery removed). Approved: the `inngest` library. Trade-offs accepted: an outside service, and jobs must finish within a web request (UniFlow's take seconds). The daily jobs use Inngest's schedule (cron, Kuala Lumpur time) instead of Celery Beat.
