# 10 — Testing Strategy & Deployment

## 20. Testing strategy

### How each task is verified

Every roadmap task lists its own verification steps (see [11](11-roadmap.md#development-workflow)). A task is complete only when:

- its checks pass locally,
- the relevant parts of the whole suite still pass (`pytest` for backend changes; `npm run lint`, `npm run typecheck` and `npm test` for frontend changes).

### Backend (pytest + pytest-django, approved; factory_boy deferred)

| Layer | What is tested | Example |
|---|---|---|
| Models | Constraints and derived values | A mismatched publisher raises `IntegrityError`, and `ApplicationListing.status_at()` behaves correctly at every boundary |
| Selectors | **Visibility**, the most important suite | A table-driven matrix of student profile × audience → visible or not, covering empty audiences, AND and OR, incomplete profiles, drafts and expired items |
| Policies and capabilities | `capabilities_for`, `manageable_queryset`, `can_manage` | Every role × resource × school |
| Manage API | Server-side enforcement | For every manage endpoint: a student gets 403, school staff get 404 on another school's item, and publishing as a school they don't belong to returns 403 |
| Read API | Shape, filters, 404 for invisible items | |
| Services | Side effects | Publishing an important announcement creates exactly N notifications, and publishing it again creates none |
| Timetable | Time zone and import logic | Local "today" around midnight in Kuala Lumpur, plus the create, update and unchanged cases in an import dry run |

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
| Staging and production | A single Linux VM, or the university's own server (*hosting still to be decided*) |

### Recommended MVP topology

```
 HTTPS ─► nginx (or Caddy) ─┬─ uniflow.example.edu      → frontend/dist (static files from `npm run build`)
                            └─ api.uniflow.example.edu  → gunicorn (systemd service) → Django
                                                         /media/posters/ served by nginx (public)
                                                         documents streamed by Django (logged-in only)
        MySQL 8.4 (same VM, native)   ·   nightly mysqldump + media backup → off-site
```

- A Pipenv-managed virtualenv with gunicorn, run as a systemd service. nginx serves the Django admin's static files after `collectstatic`. whitenoise is deferred, and is added in M10.7 only if the final deployment design needs it.
- Release steps:
  1. `git pull`
  2. `pipenv sync` (installs exactly what `Pipfile.lock` pins, with no dev packages)
  3. `manage.py migrate`
  4. `collectstatic`
  5. restart gunicorn
  6. `npm ci && npm run build`
- There is **no cron** in the MVP. Cron arrives with scheduled publishing and reminders.
- `manage.py check --deploy` must pass. A monitor watches `/api/v1/health/`.
- **Backups:** a daily `mysqldump` plus media, kept for 30 days. Restoring is tested once per term.
- The API domain and `/api/v1/` must stay stable once a mobile build ships.
