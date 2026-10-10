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

- **`backend.yml`:** ruff, `manage.py check`, `makemigrations --check` and pytest. `pip-audit` is optional and needs approval. MySQL runs as a GitHub Actions *service*. This uses GitHub's hosted runner, and no Docker files are added to the repo.
- **`frontend.yml`:** lint, typecheck, test and build.
- *[Later]* end-to-end tests with Playwright.

## 21. Deployment considerations

There is no Docker in the current plan. Containerization can be revisited if the hosting environment needs it.

### Environments

| Environment | Setup |
|---|---|
| Local | Native MySQL 8.4, `python manage.py runserver`, `npm run dev` |
| Staging and production | A single Linux VM, or the university's own server (*hosting still to be decided*). The WhatsApp connector needs a machine that stays online. |

### Recommended MVP topology

```
 HTTPS ─► nginx (or Caddy) ─┬─ uniflow.example.edu      → frontend/dist (static files from `npm run build`)
                            └─ api.uniflow.example.edu  → gunicorn (systemd service) → Django
                                                         /api/v1/internal/ blocked from the internet
        systemd services on the same VM:
          gunicorn (Django)  ·  celery worker  ·  celery beat  ·  redis-server  ·  whatsapp-connector
        MySQL 8.4 (same VM, native)   ·   nightly mysqldump + media backup → off-site
```

- A Pipenv-managed virtualenv with gunicorn, run as a systemd service. nginx serves the Django admin's static files after `collectstatic`. whitenoise is deferred, and is added in M9.6 only if the final deployment design needs it.
- Release steps:
  1. `git pull`
  2. `pipenv sync` (installs exactly what `Pipfile.lock` pins, with no dev packages)
  3. `manage.py migrate`
  4. `collectstatic`
  5. restart gunicorn
  6. `npm ci && npm run build`
- There is **no cron**: Celery Beat starts the daily jobs (the digest and retention clean-up). Redis, the Celery worker and Celery Beat run as services next to gunicorn. Tests and CI don't need Redis (jobs run immediately).
- The WhatsApp connector runs as its own systemd service and restarts automatically. Its login session files are kept outside the repository and backed up.
- `manage.py check --deploy` must pass (M9.5: it does with `config/settings/prod.py`, and CI checks it on every push). Production is HTTPS-only: nginx handles HTTPS and must pass `X-Forwarded-Proto: https` to Django; `http://` is redirected (except `/api/v1/health/`); HSTS starts at one hour (`DJANGO_HSTS_SECONDS`) and is raised to a year once HTTPS works; the admin login and CSRF cookies are HTTPS-only (the refresh-token cookie already was). A monitor watches `/api/v1/health/`.
- **Backups:** a daily `mysqldump` plus media, kept for 30 days. Restoring is tested once per term.
- The API domain and `/api/v1/` must stay stable once a mobile build ships.
