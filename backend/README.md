# UniFlow Backend

The Django + Django REST Framework API for UniFlow. See [docs/](../docs/README.md) for the architecture.

## Setup (Windows, PowerShell)

Requires Python 3.12+. Run these commands from the `backend/` folder:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python manage.py check
```

`check` should report `System check identified no issues (0 silenced).`

> If PowerShell blocks `Activate.ps1`, run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once, then try again.

## Status

- **M0.3:** bare Django 5.2 project (`config/`). Default settings, and no database connection yet.
- **Do not run `migrate` yet.** The custom user model (M0.6) must exist before the first migration.
- MySQL connection and environment settings arrive in M0.4.
