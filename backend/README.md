# UniFlow Backend

The Django + Django REST Framework API for UniFlow. See [docs/](../docs/README.md) for the architecture.

## Setup (Windows, PowerShell)

Requirements:

- Python 3.13
- [Pipenv](https://pipenv.pypa.io/): `python -m pip install --user pipenv`
- A local MySQL 8.x server with a `uniflow` database ([docs/development-setup.md](../docs/development-setup.md#1-local-database))

Dependencies live in `Pipfile` (the ranges you allow) and `Pipfile.lock` (exact pinned versions and hashes). Both are committed.

**Keep the virtual environment inside `backend/.venv`** (it is git-ignored). Set this once for your user account, then open a new terminal:

```powershell
[Environment]::SetEnvironmentVariable("PIPENV_VENV_IN_PROJECT", "1", "User")
```

Run these commands from the `backend/` folder:

```powershell
pipenv sync --dev                # create .venv and install exactly what Pipfile.lock pins
Copy-Item .env.example .env      # then edit .env: DB_USER, DB_PASSWORD and DJANGO_SECRET_KEY
pipenv run python manage.py check
pipenv run python manage.py showmigrations
```

`check` should report `System check identified no issues (0 silenced).`

To avoid typing `pipenv run` every time, open a shell inside the environment with `pipenv shell`, then run `python manage.py ...` directly.

> Pipenv also loads `backend/.env` automatically for `pipenv run` and `pipenv shell`. That is consistent with `config/env.py`, which never overrides variables that are already set.

### Tests and linting

```powershell
pipenv run pytest                  # uses config.settings.test; creates and drops the test_uniflow database
pipenv run ruff check .            # lint
pipenv run ruff format .           # format (use --check to verify without changing files)
```

Tests run against **MySQL**, not SQLite. The MySQL account in `.env` must be able to create and drop `test_uniflow`. Tool configuration is in `pyproject.toml`.

### Adding a dependency

Only add a dependency in the roadmap task that needs it, and only once it is approved:

```powershell
pipenv install "package>=x.y,<x.z"          # runtime dependency
pipenv install --dev "package>=x.y,<x.z"    # development-only tool
```

Commit `Pipfile` and `Pipfile.lock` together.

## Configuration

| Item | Where |
|---|---|
| Settings modules | `config/settings/base.py` (shared), `dev.py` (the default for `manage.py`), `test.py` (pytest), `prod.py` (the default for `wsgi.py`/`asgi.py`) |
| Environment variables | `backend/.env`, loaded by `config/env.py`. Copy it from `.env.example`. Real environment variables win. `.env` is never committed. |
| Django admin | `/django-admin/`. A back-office for developers and super admins only. |

## API

| URL | What it is |
|---|---|
| `/api/v1/health/` | Public health check: `{"status": "ok", "db": "ok"}`, or HTTP 503 if MySQL is unreachable |
| `/api/v1/docs/` | Swagger UI. **Development only** (`DJANGO_DEBUG=true`). |
| `/api/v1/schema/` | The OpenAPI 3 schema. Development only. |

- **Error format:** every API error is `{"error": {"code": "...", "message": "...", "fields": {...}}}`. `fields` holds per-field validation messages and is `{}` for other errors.
- **Defaults:** JSON only, login required (`IsAuthenticated`) unless a view allows public access, 20 items per page (`?page=`, `?page_size=`, at most 100), and rate limits of 30/min anonymous, 300/min authenticated and 10/min for `auth`-scoped views.
- **CORS:** only the origins in `CORS_ALLOWED_ORIGINS` may call the API from a browser. In dev that defaults to the Vite server (`localhost:5173`).

## Logging in (API)

Accounts use **Djoser's own URLs**. Login and refresh use SimpleJWT with one change (`apps/accounts/cookie_jwt.py`): **the refresh token is kept in a secure httpOnly cookie** (`uniflow_refresh`), so page scripts can never read it.

- `POST /api/v1/auth/jwt/create/` with `{"email", "password"}` returns `{access}` and sets the refresh-token cookie.
- Send `Authorization: Bearer <access>` on every request. In the Swagger docs, click **Authorize** and paste the access token.
- The access token lasts 15 minutes. `POST /api/v1/auth/jwt/refresh/` (no body; the browser sends the cookie) returns a new `{access}` and a new cookie.
- `POST /api/v1/auth/jwt/logout/` cancels the refresh token and deletes the cookie.

## Emails in development

Emails (for example the activation email after registering) are **printed in the `runserver` terminal** instead of being sent. Copy the link from there. Real sending is set up at deployment (M10).

## Background jobs (Celery + Redis)

Slow work (the AI, daily summaries) runs in a Celery **worker**, with **Redis** holding the to-do
list. Tests don't need either: jobs run immediately there.

1. Start Redis in WSL (install once with `sudo apt install redis-server`):

   ```bash
   sudo service redis-server start
   redis-cli ping            # answers PONG
   ```

2. Start the worker from `backend/` on Windows (`--pool=solo` is needed on Windows):

   ```powershell
   pipenv run celery -A config worker --pool=solo -l info
   ```

3. Check the set-up from a second terminal; the worker's window shows `succeeded ... 'pong'`:

   ```powershell
   pipenv run celery -A config call config.celery.ping
   ```

4. Daily jobs (added in later milestones) need Celery Beat too: `pipenv run celery -A config beat -l info`.

`CELERY_BROKER_URL` defaults to `redis://127.0.0.1:6379/0`. Use `127.0.0.1`, not `localhost`: on
Windows `localhost` tries IPv6 first, which WSL doesn't forward, and each connection waits ~20 s.

## Background jobs with Inngest (replacing Celery, from M9.6j)

UniFlow is moving its background jobs from Celery to **Inngest**, one group at a time; until
that's finished, start both. With Inngest there is no worker and no Redis: Inngest calls Django
at `/api/inngest` to run each job (code: `config/inngest.py`). Tests need neither.

1. With `runserver` running, start Inngest's dev server from any folder (needs Node; it is
   downloaded the first time):

   ```powershell
   npx --ignore-scripts=false inngest-cli@1.45.1 dev --no-discovery -u http://127.0.0.1:8000/api/inngest
   ```

2. Open its dashboard at http://127.0.0.1:8288: **Apps** shows `uniflow` as synced.
3. Check the set-up from `backend/`; the dashboard's **Runs** shows `ping` completed with `pong`:

   ```powershell
   pipenv run python manage.py inngest_ping
   ```

`INNGEST_DEV` is `true` by default on your laptop (`config.settings.dev`) and `false` online,
where Inngest Cloud's `INNGEST_SIGNING_KEY` and `INNGEST_EVENT_KEY` are needed.

## Database migrations

UniFlow uses a custom, email-based user model (`accounts.User`, `AUTH_USER_MODEL = "accounts.User"`). There is no `username`.

```powershell
pipenv run python manage.py migrate
pipenv run python manage.py createsuperuser   # prompts for email, full name and password
```

The super admin can then log in to the back-office at `http://127.0.0.1:8000/django-admin/` (run `pipenv run python manage.py runserver` first).

> **If you ran `migrate` before M0.6,** your database contains Django's default `auth_user` tables and `migrate` will fail with `InconsistentMigrationHistory`. The database has no real data yet, so drop and recreate it (see [docs/development-setup.md](../docs/development-setup.md#1-local-database)) and run `migrate` again.
