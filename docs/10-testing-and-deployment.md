# 10 — Testing Strategy & Deployment

## 20. Testing strategy

### How each task is verified

Every roadmap task lists its own verification steps (see [11](11-roadmap.md#development-workflow)). A task is complete only when:

- its checks pass locally,
- the relevant parts of the whole suite still pass (`pytest` for backend changes; `npm run lint`, `npm run typecheck` and `npm test` for frontend changes).

### Backend (pytest + pytest-django, approved; factory_boy deferred)

| Layer | What is tested | Example |
|---|---|---|
| Models | Constraints and derived values | A mismatched publisher raises `IntegrityError`; the worked-out semester is correct for each intake and date |
| Selectors | **Who is affected**, the most important suite | A table-driven matrix of student profile × audience (including courses, sections, semesters and group members) → reached or not, covering empty audiences, AND and OR, incomplete profiles, drafts and expired insights |
| Policies and capabilities | `capabilities_for`, `manageable_queryset`, `can_manage` | Every role × resource × school |
| Manage API | Server-side enforcement | For every manage endpoint: a student gets 403, school staff get 404 on another school's item, and publishing as a school they don't belong to returns 403 |
| Read API | Shape, filters, 404 for invisible items | |
| Services | Side effects | Publishing an important insight creates exactly N notifications, and publishing it again creates none; confidence below 0.5 creates a draft and no deliveries |
| Timetable | Time zone, import logic, confirmed changes | Local "today" around midnight in Kuala Lumpur; import dry runs; a student's day = official meetings + only *their* confirmed changes |
| Intelligence | The pipeline with a **fake provider** (never the real AI in tests) | Invalid model output is rejected; course codes resolve; ambiguous names are not mentions; duplicates merge without a second notification; relevance and tier rules per student |
| AI evaluation | The real model against labelled, anonymized messages | `manage.py evaluate_intelligence` reports accuracy per kind. Run by hand when prompts or models change, **not in CI** (it costs money and needs the API key). |
| Ingestion | Webhook and connector endpoints | Wrong secret → 403; the same message twice → stored once; chat-export parsing; private messages to the connector are ignored |
| Timetable imports | Reading and applying | With a fake provider: rows are shown, nothing is saved before confirm, confirm creates missing classes and enrols, existing classes are never overwritten; Google Drive links outside the allowed hosts are refused |

- **Tests run against MySQL** (the local `test_uniflow` database), not SQLite, because collation and strict mode behave differently.
- The coverage target is **at least 90% on `selectors`, `policies` and `services`**. There is no global target.

### Frontend (Vitest + React Testing Library, approved)

- **Units:** date and format helpers, Zod schemas, `platformLinks`, capability helpers
- **Components:** the loading, error, empty and data states; `RequireCapability` and `Can` hide or allow correctly; the `AudienceFields` summary
- **Auth:** a 401 triggers one refresh and a retry, and a failed refresh logs the user out. Axios is mocked with `vi.mock`, so no extra mocking library is needed.

### Continuous integration (GitHub Actions, `.github/workflows/`)

- **`backend.yml`:** ruff, `manage.py check`, `makemigrations --check`, `check --deploy` with the production settings, and pytest on **MySQL**; a second job runs every test on **PostgreSQL** (the production database, M9.6b). `pip-audit` is optional and needs approval. MySQL runs as a GitHub Actions *service*. This uses GitHub's hosted runner (the Docker setup in `deploy/` is for running UniFlow, not for CI).
- **`frontend.yml`:** lint, typecheck, test and build.
- *[Later]* end-to-end tests with Playwright.

## 21. Deployment considerations

> Production setup, configuration and free-tier trade-offs: **[deployment.md](deployment.md)** (M9.6n).

**Decided (M9.6):** the **backend runs on Render** from Docker images, the **website on Vercel** (Vercel builds `frontend/` itself; no Docker), and the **production database is PostgreSQL** (Render has no MySQL; development stays on MySQL). M9.6b made the code ready for it (PostgreSQL, whitenoise, the Vercel forwarding below); uploaded files live in **Supabase Storage** (M9.6h, below), because Render's services don't share a disk. The step-by-step Render guide comes next.

### Environments

| Environment | Setup |
|---|---|
| Local development | Native MySQL 8.4, `python manage.py runserver`, Inngest's dev server (`npx inngest-cli dev`), `npm run dev` |
| Trying the online backend locally | Docker Desktop: `docker compose up` in `deploy/` (the same images Render runs) |
| Production ($0, M9.6n) | **Render** (free, Singapore): the backend image as a web service (Django on gunicorn, which also runs the background jobs when Inngest calls it). **Supabase** (free, Singapore): PostgreSQL and file storage. **Inngest Cloud:** starts the background jobs. **Vercel:** the website. **WhatsApp connector:** on the developer's computer for now (Render's free plan sleeps and has no disk for its login); later a free cloud computer. No Celery worker, Beat or Redis (removed in M9.6m). |

### How the two hosts fit together: Vercel forwarding (M9.6b)

```
 browser ─► https://<name>.vercel.app/timetable      → Vercel: the website
 browser ─► https://<name>.vercel.app/api/v1/feed/   → Vercel forwards to → https://<name>.onrender.com/api/v1/feed/
```

The browser only ever talks to the **Vercel address**, so the login cookie is a normal same-site cookie that every browser (including Safari, which blocks cookies from other sites) keeps. Set up by `frontend/vercel.json` ("rewrites to an external origin") and `frontend/.env.production` (`VITE_API_URL=/api/v1`, used by `npm run build`). No CORS is needed for the website.

- **No caching of personal data:** `vercel.json` switches Vercel's caching off for `/api/` (`x-vercel-enable-rewrite-caching: 0`), and Django marks every `/api/` answer `Cache-Control: private, no-store` (`core/middleware.py`).
- **Visitor addresses:** Vercel sends the visitor's address first in `X-Forwarded-For`; Django's rate limits use it, so one student's failed logins never slow down everyone (tested in `core/tests/test_hosting.py`). Login is limited to 10 attempts a minute per visitor (`throttle_scope = "auth"`, now actually applied).
- **Limits to know:** Vercel waits up to 120 seconds for Render to start answering (a sleeping free Render service can take most of that); request size through the forwarding must be tested with a 10 MB timetable upload (Vercel functions allow 4.5 MB), and if it fails, uploads go straight to Render or `MAX_UPLOAD_MB` is lowered.
- **Direct addresses:** the Django admin (`https://<name>.onrender.com/django-admin/`), the Telegram webhook and the WhatsApp connector use the Render address directly.
- **After creating the Render service,** put its real address in `frontend/vercel.json` (`destination`), commit and push; Vercel redeploys by itself.

### The Docker images

| Image | Built from | Runs |
|---|---|---|
| Backend | `backend/Dockerfile` (Python 3.13, `pipenv install --deploy`, gunicorn, a non-root user) | Django (with whitenoise serving the admin's styles, production settings only); background jobs run inside it when Inngest calls `/api/inngest`. Each start runs `migrate` and `collectstatic`, then gunicorn on `$PORT` (Render) or 8000, with 2 workers and a 120-second limit per request (AI jobs can take over 30 s) |
| WhatsApp connector | `connectors/whatsapp/Dockerfile` (Node 24, a non-root user) | UniFlow's WhatsApp number; its login lives in `/app/auth` (a disk or volume) |

Each has a `.dockerignore`, so secrets (`.env`) and the WhatsApp login (`auth/`) never go into an image; settings are given when a container starts.

### Uploaded files online: Supabase Storage (M9.6h)

Timetable images, PDFs and spreadsheets are saved when a student uploads them and read later by a background job. On Render a service's disk is temporary and not shared (and was not shared with the old worker), so online they go to one **private Supabase Storage bucket** that every copy of the service reaches. Supabase speaks the same language as Amazon S3, so Django uses it through `django-storages` (with `boto3`); nothing else in the code changes. The same five `S3_…` settings also work on your laptop (in `backend/.env`); with `S3_BUCKET` empty, files stay on the disk (`backend/media/`). **Tests always use the disk**, whatever `.env` says. Tip: use a separate bucket for your laptop (e.g. `uniflow-files-dev`) so test uploads never mix with students' files.

**Set it up once (about 5 minutes):**

1. At [supabase.com](https://supabase.com), create a project. Pick the **Southeast Asia (Singapore)** region, the closest to Malaysia.
2. **Storage → New bucket**, named e.g. `uniflow-files`, with **Public bucket turned off** (it must stay private).
3. **Storage → Settings → S3 connection** (on older dashboards: Project Settings → Storage): copy the **Endpoint** (`https://<project-ref>.storage.supabase.co/storage/v1/s3`) and the **Region** (e.g. `ap-southeast-1`), then **New access key** and copy the **Access key ID** and **Secret access key**. The secret is only shown once.
4. In Render, give the **web service** these settings: `S3_BUCKET`, `S3_ENDPOINT_URL`, `S3_REGION`, `S3_ACCESS_KEY_ID`, `S3_SECRET_ACCESS_KEY`. **Never** put them in git or a screenshot: the key can read and delete every file in the project's storage.
5. Check: upload a timetable image on the Timetable page; it appears in Supabase under `uniflow-files/message_files/<year>/<month>/`, and its classes are read by the background job. After `MESSAGE_RETENTION_DAYS` it disappears from the bucket.

**Good to know (free plan):** 1 GB of storage (plenty: 10 MB per file, deleted after 60 days) and 50 MB per file. A free project **pauses after about a week without activity** (e.g. a semester break); uploads then fail until you press **Restore** in the Supabase dashboard. If the key leaks: delete it in Supabase, create a new one, update Render.

### Background jobs online: Inngest Cloud (from M9.6j)

UniFlow's background jobs run on Inngest (M9.6j–m), so online there is **no worker, no Beat and no Redis**: Inngest Cloud calls the web service at `https://<name>.onrender.com/api/inngest` to run each job. The full set-up (create the app at app.inngest.com, give Render `INNGEST_SIGNING_KEY` and `INNGEST_EVENT_KEY`, sync the app) is part of the Render guide. **Production refuses to start without both keys** (the error names the missing one). Calls without Inngest's signature are refused (401), so nobody else can start a job. Uploaded files are shared through Supabase Storage (above), since the jobs may run in any copy of the web service.

### Trying the backend locally with Docker Desktop (`deploy/docker-compose.yml`)

Not used by Render: it starts the same images on your computer, with **PostgreSQL**, so you can see the backend run as it will online. Background jobs: start **Inngest's dev server on your computer** (command in `backend/README.md`, with `-u http://localhost:8000/api/inngest`); `INNGEST_DEV` in `deploy/.env` lets the backend container reach it.

1. In `deploy/`: `Copy-Item .env.example .env`, then fill in `DJANGO_SECRET_KEY`, `DB_PASSWORD` (letters and digits), `GEMINI_API_KEY` (and `CONNECTOR_SECRET`, `WHATSAPP_NUMBER` for WhatsApp). `.env` is git-ignored.
2. `docker compose up -d --build` (add `--profile whatsapp` for the connector). `backend` runs `migrate` and `collectstatic`, then gunicorn.
3. `docker compose exec backend python manage.py createsuperuser`, then open `http://localhost:8000/api/v1/health/` and `http://localhost:8000/django-admin/`. The website runs with `npm run dev` as usual.

Useful: `docker compose ps`, `docker compose logs -f backend`, `docker compose down` (the data stays in volumes). **Never** `docker compose down -v`: it deletes the volumes (the database and the WhatsApp login).

- `manage.py check --deploy` must pass (M9.5: it does with `config/settings/prod.py`, and CI checks it on every push). Production is HTTPS-only: the host (Render) handles HTTPS and passes `X-Forwarded-Proto: https`; `http://` is redirected (except `/api/v1/health/` and the connector's `/api/v1/internal/` on the private network, whose requests are signed); HSTS starts at one hour (`DJANGO_HSTS_SECONDS`) and is raised to a year once HTTPS works; the admin login and CSRF cookies are HTTPS-only.
- **Backups:** daily PostgreSQL backups (Supabase's free plan keeps a few days; a weekly `pg_dump` from your laptop adds safety), plus the WhatsApp login folder (`connectors/whatsapp/auth/`), kept for 30 days; uploaded files live in Supabase Storage and are short-lived (deleted after `MESSAGE_RETENTION_DAYS`), the classes read from them are in the database. Restoring is tested once per term. *(Set up with hosting.)*
- The API domain and `/api/v1/` must stay stable once a mobile build ships.
