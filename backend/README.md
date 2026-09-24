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

## Database migrations

UniFlow uses a custom, email-based user model (`accounts.User`, `AUTH_USER_MODEL = "accounts.User"`). There is no `username`.

```powershell
pipenv run python manage.py migrate
pipenv run python manage.py createsuperuser   # prompts for email, full name and password
```

The super admin can then log in to the back-office at `http://127.0.0.1:8000/django-admin/` (run `pipenv run python manage.py runserver` first).

> **If you ran `migrate` before M0.6,** your database contains Django's default `auth_user` tables and `migrate` will fail with `InconsistentMigrationHistory`. The database has no real data yet, so drop and recreate it (see [docs/development-setup.md](../docs/development-setup.md#1-local-database)) and run `migrate` again.
