# UniFlow Backend

The Django + Django REST Framework API for UniFlow. See [docs/](../docs/README.md) for the architecture.

## Setup (Windows, PowerShell)

Requires Python 3.12+ and a local MySQL 8.x server with a `uniflow` database ([docs/development-setup.md](../docs/development-setup.md#1-local-database)). Run these commands from the `backend/` folder.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt

Copy-Item .env.example .env      # then edit .env: set DB_PASSWORD and DJANGO_SECRET_KEY
python manage.py check
python manage.py showmigrations  # connects to MySQL; lists Django's built-in apps as unapplied
```

`check` should report `System check identified no issues (0 silenced).` `showmigrations` should list the `admin`, `auth`, `contenttypes` and `sessions` migrations, all unapplied (`[ ]`), without a connection error.

> If PowerShell blocks `Activate.ps1`, run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once, then try again.

## Configuration

| Item | Where |
|---|---|
| Settings modules | `config/settings/base.py` (shared), `dev.py` (the default for `manage.py`), `test.py` (pytest), `prod.py` (the default for `wsgi.py`/`asgi.py`) |
| Environment variables | `backend/.env`, loaded by `config/env.py`. Copy it from `.env.example`. Real environment variables win. `.env` is never committed. |
| Django admin | `/django-admin/`. A back-office for developers and super admins only. |

## Status

- **Do not run `migrate` yet.** The custom user model (M0.6) must exist before the first migration.
