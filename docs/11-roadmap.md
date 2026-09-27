# 11 — Roadmap & Implementation Tasks (M0–M10)

## Development workflow

UniFlow is built **one small task at a time**.

1. **One task per request.** Claude implements exactly one task from this roadmap and changes only the files listed for it. Anything outside the task, such as a refactor or a "while I'm here" fix, is proposed, not done.
2. **Stop after the task.** Claude reports:
   - the files that changed,
   - the verification steps,
   - the suggested commit message,
   - the exact Git commands to stage, verify (`git diff --cached`) and commit,
   - anything that needs a decision.

   Claude then **stops**.
3. **The developer reviews and commits on `main`.** The developer reads the diff, runs the checks, stages the files and commits. **Claude never stages, commits, pushes or creates branches** unless asked to explicitly.
4. **The developer says "proceed"** before the next task starts.
5. **No surprise dependencies.** A task installs only the libraries listed on its card. If a library is not yet approved, Claude asks before installing it.
6. **Tests ship with the code** in the same task. If a task cannot be tested automatically, its card says how to verify it by hand.
7. **Docs change with the contract.** If a task changes an API shape or model, the relevant doc is updated in the same task.
8. **Split big tasks.** If a task grows beyond about 10 files, or needs both backend and frontend work that could be verified separately, it is split before it starts.

**Commit format:** [Conventional Commits](https://www.conventionalcommits.org/), `type(scope): summary`. For example: `chore(repo): add repository conventions`, `feat(auth): add custom user model` or `feat(frontend): initialize react application`.

**Branching:** all work is committed directly on **`main`**, one small commit per task. No feature or task branches are used unless the developer explicitly asks for one.

**Task cards.** Every task in M0 has a full card below. Tasks in M1–M10 are listed in tables. Each milestone's tables are expanded into full cards (objective, prerequisites, files, implementation, verification, integration, commit) when that milestone begins, because the details depend on decisions made in earlier milestones.

## Milestones

| Milestone | Name | Outcome |
|---|---|---|
| **M0** | Foundations | An empty Django API and an empty React app, both running locally and in CI |
| **M1** | Identity | Register, activate, log in, onboard and edit the profile |
| **M2** | Permissions, publishing core and staff dashboard shell | Capabilities, audience visibility, the shared content base, the `/staff` layout and user and reference-data management |
| **M3** | Announcements | The first full feature: student feed plus staff management |
| **M4** | Documents | Document library, downloads and announcement attachments |
| **M5** | Events | Event list, calendar and staff management |
| **M6** | Communities | Directory, WhatsApp and Telegram links, follow and staff management |
| **M7** | Timetable | Staff-maintained timetable data, the import service, section selection, and today and week views |
| **M8** | Applications and forms | Listings with a derived status, plus staff management |
| **M9** | Notifications | In-app notifications when content is published |
| **M10** | Dashboard, search and release | The student dashboard, global search, staff home, production settings and deployment |
| — | **MVP release** | |
| Later | Post-MVP | See [Later backlog](#later-backlog) |

---

## M0 — Foundations

#### M0.1 — Repository conventions
- **Purpose:** Set rules that apply to the whole repository, and nothing else.
- **Prerequisites:** None.
- **Files:**
  - `.gitattributes`: `* text=auto eol=lf`, plus binary rules for images and PDFs.
  - `.editorconfig`: UTF-8, LF, final newline; 4 spaces for `*.py`, 2 spaces for `*.{ts,tsx,js,json,css,md,yml}`.
  - `.gitignore` at the root: **operating system and editor files only** (`.DS_Store`, `Thumbs.db`, `.idea/`, `*.swp`, `.vscode/*` except shared settings).
  - `README.md`: a "Getting started" section with links to the setup docs that later tasks add.
- **Not included:** backend or frontend ignores, which belong to M0.3 and M0.9, and no Docker files.
- **Verification:** `git status` shows only these files. `git check-attr eol -- README.md` reports `lf`.
- **Integration:** Every later task follows these conventions.
- **Commit:** `chore(repo): add repository conventions`

#### M0.2 — Local database (manual step, no commit)
- **Decision:** there is no setup script. Each developer creates the database themselves in their existing local MySQL server, and Django connects to it with the settings from M0.4.
- **Requirements:**
  - MySQL 8.x is running locally.
  - A database named **`uniflow`** exists and uses `utf8mb4`. This is the MySQL 8 default. Example: `CREATE DATABASE uniflow CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;`
  - The MySQL account Django uses can create and drop the `test_uniflow` database. pytest needs this from M0.5 onwards. Root can do this, and a dedicated user needs `ALL` on `test_uniflow.*`.
- **Documented in:** [development-setup.md](development-setup.md#1-local-database).

#### M0.3 — Django project initialization
- **Purpose:** Create a bare Django 5.2 project inside `backend/`.
- **Prerequisites:** M0.1.
- **Files:**
  - `backend/requirements.txt` (`Django>=5.2,<5.3`). Replaced by `Pipfile` in M0.4a.
  - `backend/.gitignore` (`.venv/`, `__pycache__/`, `*.pyc`, `.env`, `media/`, `staticfiles/`, `.pytest_cache/`, `.ruff_cache/`, `.coverage`)
  - `backend/manage.py` and `backend/config/{__init__,settings,urls,wsgi,asgi}.py`, created by `django-admin startproject config .`
  - `backend/README.md`: backend setup steps (venv, install, check). Backend-only documentation lives with the backend.
- **Implementation:** Use the default settings. **Do not run `migrate`**, because the custom user model must come first (M0.6).
- **Verification:** `python -m venv .venv`, activate it, `pip install -r requirements.txt`, then `python manage.py check` reports "System check identified no issues".
- **Integration:** M0.4 restructures the settings.
- **Commit:** `feat(backend): initialize django project`

#### M0.4 — Backend configuration
- **Purpose:** Split the settings by environment, read configuration from `.env`, and connect to MySQL.
- **Prerequisites:** M0.3, plus the local `uniflow` database (M0.2).
- **Libraries:** `mysqlclient` only. **No `django-environ`:** configuration comes from a small `config/env.py` helper that uses only the standard library.
- **Files:**
  - `backend/config/settings/{__init__,base,dev,test,prod}.py`, replacing `settings.py`
  - `backend/config/env.py`: reads `backend/.env` if it exists (`KEY=VALUE` lines, `#` comments), never overrides real environment variables, and provides `env_str`, `env_bool` and `env_list`
  - `backend/.env.example`
  - `backend/requirements.txt` (adds `mysqlclient`; moved into `Pipfile` in M0.4a)
  - `backend/apps/__init__.py` and `backend/core/__init__.py`, as empty packages
  - `manage.py` defaults to `config.settings.dev`. `wsgi.py` and `asgi.py` default to `config.settings.prod`, so a server that forgets `DJANGO_SETTINGS_MODULE` fails safe.
  - `config/urls.py` (the admin moves to `/django-admin/`) and `backend/README.md` (the `.env` setup steps)
- **Implementation:**
  - `DATABASES` is built from `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST` and `DB_PORT`, with utf8mb4 and strict-mode `OPTIONS`.
  - `TIME_ZONE` comes from the environment, with `USE_TZ=True`.
  - `MEDIA_ROOT` and `MEDIA_URL` are set.
  - The admin URL moves to `/django-admin/`.
  - `prod.py` requires `DJANGO_SECRET_KEY` and `DJANGO_ALLOWED_HOSTS`.
- **Verification:**
  1. Copy `.env.example` to `.env`.
  2. `python manage.py check` passes.
  3. `python manage.py showmigrations` connects to MySQL without errors.
  4. Do **not** migrate yet.
- **Integration:** Every backend task after this uses these settings.
- **Commit:** `chore(backend): configure settings, environment and mysql`

#### M0.4a — Switch dependency management to Pipenv (done)
- **Purpose:** Manage backend dependencies with Pipenv instead of `venv` plus `requirements.txt`, as the developer chose.
- **Files:** adds `backend/Pipfile` and `backend/Pipfile.lock`, and deletes `backend/requirements.txt`. Updates `backend/README.md` and the docs that mention installing.
- **Implementation:** `PIPENV_VENV_IN_PROJECT=1` keeps the environment in `backend/.venv`, which is already git-ignored. The runtime packages are `django>=5.2,<5.3` and `mysqlclient>=2.2,<2.3`, and the Python version is `3.13`. Pipenv also loads `backend/.env` automatically, which is compatible with `config/env.py`.
- **Verification:** `pipenv sync --dev`, `pipenv run python manage.py check`, `pipenv run python -c "import MySQLdb"`.
- **Commit:** `chore(backend): switch dependency management to pipenv`

#### M0.5 — Backend test and lint tooling
- **Purpose:** Make `pytest` and `ruff` available before any real code is written.
- **Prerequisites:** M0.4a.
- **Libraries:** these Pipenv `[dev-packages]`, all approved:
  - `pytest>=9.1,<10`
  - `pytest-django>=4.14,<5`
  - `ruff>=0.16,<0.17`. Ruff is pinned to its minor version because its 0.x releases can change formatting and lint rules.

  `factory_boy` is deferred.
- **Files:**
  - `backend/Pipfile` and `Pipfile.lock`
  - `backend/pyproject.toml`: tool configuration only
    - `[tool.ruff]`: py313, line length 100, migrations excluded, and the rule sets E, F, I, UP, B and DJ
    - `[tool.pytest.ini_options]`: `DJANGO_SETTINGS_MODULE=config.settings.test`
  - `backend/tests/__init__.py` and `backend/tests/test_smoke.py`
  - `backend/README.md`
  - A one-time `ruff format` of the existing files (the Django-generated `manage.py`, `wsgi.py`, `asgi.py` and `urls.py`, plus one long line in `env.py`). This changes style only.
  - There is no `conftest.py` yet. It will be added when there are shared fixtures.
- **Verification:**
  1. `pipenv run pytest` passes 3 tests: the settings module, MySQL with utf8mb4, and a query against `test_uniflow`.
  2. `pipenv run ruff check .` and `pipenv run ruff format --check .` are clean.
  3. `manage.py check` and `makemigrations --check --dry-run` are unchanged.
- **Integration:** Every backend task adds tests.
- **Commit:** `chore(backend): add pytest and ruff tooling`

#### M0.6 — Custom user model
- **Purpose:** Create the email-based user with a role, before the first migration.
- **Prerequisites:** M0.5, and a **fresh** `uniflow` database. If `migrate` was ever run before this task, drop and recreate the database.
- **Files:**
  - `backend/apps/accounts/{__init__,apps,models,managers,forms,admin}.py`
  - `backend/apps/accounts/migrations/{__init__,0001_initial}.py`
  - `backend/apps/accounts/tests/{__init__,test_models}.py`
  - `config/settings/base.py`: `INSTALLED_APPS` and `AUTH_USER_MODEL`
  - `backend/README.md`
- **Implementation:**
  - `UserRole` TextChoices, also available as `User.Role`.
  - `User(AbstractUser)` with `username`, `first_name` and `last_name` removed. It has a unique `email` (the `USERNAME_FIELD`), `full_name` (required, and asked for by `createsuperuser`), `role` (indexed, default `student`) and `is_suspended`.
  - A `CheckConstraint`, `accounts_user_role_valid`.
  - `UserManager`:
    - It lowercases the **whole** email address, and `User.clean()` does the same, which covers the admin forms.
    - `create_superuser` requires `role=super_admin`, `is_staff` and `is_superuser`.
  - Uniqueness is case-insensitive at the database level too, because the `utf8mb4_0900_ai_ci` collation is case-insensitive.
  - The back-office `UserAdmin` uses email-based versions of `AdminUserCreationForm` and `UserChangeForm`.
  - `is_active` keeps Django's default of True for accounts created by admins. Djoser's registration creates users as inactive (M1.5).
- **Verification:**
  1. `pipenv run pytest` passes the 11 user-model tests, including case-insensitive uniqueness and the role constraint on MySQL.
  2. Ruff is clean, and `makemigrations --check` reports no changes.
  3. The developer resets the database, then runs `migrate` and `createsuperuser`, and logs in at `/django-admin/`.
- **Integration:** Profiles (M1.4), Djoser (M1.5) and capabilities (M2.1).
- **Commit:** `feat(auth): add custom user model`

#### M0.7 — API base configuration
- **Purpose:** Set up the `/api/v1/` mount, the error format, pagination, throttling, CORS, OpenAPI and the health check.
- **Prerequisites:** M0.6.
- **Libraries** (Pipenv `[packages]`, all approved):
  - `djangorestframework>=3.18,<4`
  - `django-cors-headers>=4.9,<5`
  - `drf-spectacular>=0.30,<0.31`, pinned to its minor version because it is on 0.x
- **Files:**
  - `backend/Pipfile` and `Pipfile.lock`
  - `backend/config/api_v1.py` and `config/urls.py`
  - `backend/core/{exceptions,pagination,views}.py`
  - `backend/core/tests/{__init__,test_api_base}.py`
  - `backend/conftest.py`: the first shared fixture, which clears the cache so throttle counters never leak between tests
  - `config/settings/{base,dev}.py`
  - `backend/.env.example`: adds `CORS_ALLOWED_ORIGINS`
  - `backend/README.md` and `docs/04-api.md`
- **Implementation:**
  - `REST_FRAMEWORK`:
    - no authentication classes yet (JWT arrives in M1.6), with `IsAuthenticated` as the default permission
    - JSON only, and `StandardPagination` (20 per page, at most 100)
    - the `api_exception_handler` error format
    - throttle rates: anonymous 30/min, user 300/min, `auth` 10/min
  - Views:
    - `GET /api/v1/health/` is public and returns 503 if MySQL is unreachable.
    - A catch-all route makes unknown `/api/v1/` paths return the JSON 404 error.
    - The OpenAPI schema and docs are served only when `DEBUG` is on.
  - CORS:
    - an exact list of allowed origins (dev defaults to the Vite server)
    - `CORS_ALLOW_CREDENTIALS` enabled for the M1.6 cookie
    - `x-client` allowed as a header
- **Verification:**
  1. `pytest` passes 30 tests, covering health, the error format for every error type, pagination, CORS allow and deny, and schema generation with `--fail-on-warn`.
  2. Ruff and the Django checks are clean.
  3. With `runserver`, the health check returns 200, an unknown path returns the JSON 404, `/api/v1/docs/` returns 200, and the throttle returns 429 in the error format.
- **Integration:** Every app registers its routes in `api_v1.py`, before the catch-all.
- **Commit:** `feat(api): add api v1 base configuration and health check`

#### M0.8 — Backend CI
- **Purpose:** GitHub runs the backend checks automatically on every push and pull request.
- **Prerequisites:** M0.7, and the repository pushed to GitHub.
- **Files:** `.github/workflows/backend.yml`
- **Implementation:**
  - Runs on `ubuntu-latest` with Python 3.13 and a **MySQL 8.4 service**. The service runs on GitHub's machines, and no Docker files are added to the repository.
  - Installs the Linux MySQL client headers that `mysqlclient` needs, then Pipenv, then `pipenv sync --dev`.
  - Runs `ruff check`, `ruff format --check`, `manage.py check`, `makemigrations --check --dry-run` and `pytest`.
  - Only runs when `backend/**` or the workflow file changes, and cancels older runs of the same branch.
  - CI has no `.env` file, so the `DB_*` variables and a CI-only `DJANGO_SECRET_KEY` are set in the workflow. None of them are real secrets.
  - `pip-audit` is not included, because it was never approved.
- **Verification:** push `main`. On GitHub, **Actions → Backend CI** turns green, and the commit shows a ✓.
- **Integration:** Guards `main`. The frontend gets its own workflow in M0.14.
- **Commit:** `ci(backend): add backend workflow`

#### M0.9 — Frontend initialization
- **Purpose:** Create a Vite + React + TypeScript app inside `frontend/`.
- **Prerequisites:** M0.1, and Node.js LTS (v24 on the development machine).
- **Files:**
  - `frontend/`, generated by `npm create vite@latest frontend -- --template react-ts --no-interactive`. That produced Vite 8, React 19, TypeScript 6 and **oxlint** (the template's linter, which replaces ESLint).
  - `package.json` and `package-lock.json`, `index.html`, `vite.config.ts`, the three `tsconfig*.json` files, `.oxlintrc.json`, `public/favicon.svg`, and `src/{main,App}.tsx`
  - `frontend/.gitignore`: frontend-only rules; the editor and OS rules were removed because the root file covers them. `.env` was added.
  - `frontend/.env.example`: `VITE_API_URL=http://localhost:8000/api/v1`
  - `frontend/README.md`
- **Implementation:**
  - The Vite demo was removed: logos, `App.css`, `index.css`, `icons.svg` and the counter page. `App.tsx` is now a UniFlow placeholder, and the page title is "UniFlow".
  - `"strict": true` is set explicitly. TypeScript 6 already defaults to strict mode, but it is written down so it is visible.
  - The `@/` path alias points to `src/` in both `tsconfig.app.json` and `vite.config.ts`, and no extra packages are needed for it.
  - A `typecheck` script was added.
- **Verification:**
  1. `npm install` reports 0 vulnerabilities.
  2. `npm run typecheck`, `npm run lint` and `npm run build` all pass.
  3. A temporary `@/` import type-checks and builds.
  4. `npm run dev` serves the placeholder page, titled "UniFlow".
- **Integration:** M0.10 through M0.13 build on this.
- **Commit:** `feat(frontend): initialize react application`

#### M0.10 — Tailwind CSS setup
- **Purpose:** Set up the approved styling foundation.
- **Prerequisites:** M0.9.
- **Libraries:** Tailwind CSS v4, which is approved. `tailwindcss@^4.3.3` and its official Vite connector `@tailwindcss/vite@^4.3.3` are dev dependencies because they only run at build time. Tailwind v4 needs no PostCSS config and no `tailwind.config.js`.
- **Files:**
  - `frontend/package.json` and `package-lock.json`
  - `frontend/vite.config.ts`: adds the `tailwindcss()` plugin
  - `frontend/src/styles/index.css`:
    - `@import 'tailwindcss'`
    - the `@theme` tokens: a system `font-sans` and brand colours `brand-50` through `brand-900` (indigo-blue)
    - a base `body` style (the `slate-50` background)
  - `frontend/src/main.tsx`: imports the stylesheet
  - `frontend/src/App.tsx`: the placeholder page, styled with Tailwind as a visible proof
  - `frontend/README.md`
- **Verification:**
  1. `typecheck`, `lint` and `build` pass.
  2. The built CSS contains the utilities used, and `--color-brand-600`.
  3. The dev server shows the styled card.
  4. `npm audit` reports 0 vulnerabilities.
- **Integration:** Every UI task after this.
- **Commit:** `chore(frontend): add tailwind css`

#### M0.11 — Frontend test tooling
- **Purpose:** Set up Vitest and React Testing Library.
- **Prerequisites:** M0.9.
- **Libraries** (dev dependencies):
  - Vitest `^5.0.2` and React Testing Library `@testing-library/react@^16.3.3`, both approved
  - two helpers they cannot run without:
    - `@testing-library/dom@^10.4.2`, React Testing Library's required peer
    - `jsdom@^29.1.1`, the simulated browser
  - `@testing-library/jest-dom` is **not** added.
- **Files:**
  - `frontend/package.json` and `package-lock.json`: adds the `test` script (`vitest run`) and the `test:watch` script (`vitest`)
  - `frontend/vite.config.ts`: a `test` block with `environment: 'jsdom'`, the setup file and `src/**/*.test.{ts,tsx}`
  - `frontend/src/test/setup.ts`: runs `cleanup()` after each test
  - `frontend/src/App.test.tsx`
  - `frontend/README.md`
- **Verification:**
  1. `npm test` passes 1 test.
  2. As a sanity check, a deliberately broken page makes the test fail, and it passes again once restored.
  3. `typecheck`, `lint` and `build` pass, and `npm audit` reports 0 vulnerabilities.
- **Integration:** Every frontend task adds tests.
- **Commit:** `chore(frontend): add vitest and testing library`

#### M0.12 — Routing and layout foundation
- **Purpose:** Build the route tree and the three layouts, with placeholder pages.
- **Prerequisites:** M0.10, M0.11.
- **Libraries:** React Router (approved). npm installed **v8** (`react-router@^8.4.0`). Before any code was written, its exports and lazy-route API were checked against the installed package.
- **Files:**
  - `src/main.tsx`, which stays at `src/`, the Vite convention
  - `src/app/{App,routes,navigation}.tsx|ts`
  - `src/app/layouts/{AppLayout,AuthLayout,StaffLayout}.tsx`
  - `src/app/pages/{PlaceholderPage,NotFoundPage,RouteErrorPage}.tsx`
  - `src/shared/ui/{EmptyState,ErrorState,PageLoading}.tsx`
  - `src/app/routes.test.tsx`
  - The M0.9 placeholder `src/App.tsx` and its test are deleted.
- **Implementation:**
  - `createAppRoutes()` returns a fresh route tree. It is a function rather than a constant because React Router mutates route objects when lazy routes resolve, and a shared constant made the second router in the tests show a 404.
  - The pathless root has an `errorElement` (`RouteErrorPage`) and a `hydrateFallbackElement` (`PageLoading`).
  - The three layouts are lazy, and the build emits a separate chunk for each.
  - `AppLayout` has a sidebar at `md` and wider, and a top bar plus a 5-item bottom navigation bar on phones. Both use one list, `studentNavItems`, which has short labels for mobile.
  - `AuthLayout` is a centred card with no navigation.
  - `StaffLayout` has a dark sidebar, a "Back to UniFlow" link and an empty menu, which is filled from capabilities in M2.8.
  - Unknown paths show a 404 page.
  - A `Skeleton` component is deferred until data loading exists.
- **Verification:**
  1. `npm test` passes 6 tests: the home layout with both navigation bars, the active link, the login and staff layouts, the 404 page, and the crash page. They pass on repeated runs.
  2. `typecheck`, `lint` and `build` pass, and the build produces separate layout chunks.
  3. **Manual:** at 375 px width there is no horizontal scroll, and the bottom navigation is visible.
- **Integration:** Every feature replaces a placeholder route. M0.13 adds the providers to `App.tsx`.
- **Commit:** `feat(frontend): add routing and layout foundation`

#### M0.12a — shadcn/ui setup (added at the developer's request)
- **Purpose:** Use shadcn/ui for ready-made, accessible UI components (buttons, dialogs, tables, forms), especially for the staff dashboard.
- **Libraries** (approved together with shadcn):
  - `radix-ui`, `class-variance-authority`, `cn`, `lucide-react`, `tw-animate-css` and `@fontsource-variable/geist`
  - `shadcn` as a **dev** dependency. It is the setup tool; only its stylesheet is imported, at build time.
  - `cn` was checked: it is shadcn's official package (`github.com/shadcn-ui/cn`) and has no dependencies.
- **Files:**
  - `frontend/components.json`: shadcn config. The base is Radix, the preset is "nova", and the aliases are `@/components/ui` and `@/lib`.
  - `frontend/src/lib/utils.ts`: exports `cn`
  - `frontend/src/components/ui/button.tsx`: the only component so far
  - `frontend/src/styles/index.css`: rewritten cleanly with shadcn's theme variables, **primary = UniFlow indigo**, a light grey page background, the Geist font, the brand scale kept, and dark-theme tokens ready but unused
  - `frontend/tsconfig.json`: the `@/*` path, which the shadcn tool reads
  - `frontend/.oxlintrc.json`: turns off `only-export-components` for shadcn's generated folder only
  - `NotFoundPage.tsx` and `RouteErrorPage.tsx`: now use `<Button>`
- **Command used:** `npx shadcn@latest init --base radix --template vite --preset nova --no-monorepo --no-rtl --yes`
- **Verification:**
  1. The 6 tests still pass.
  2. `typecheck` passes, and `lint` is clean with no warnings.
  3. The build passes, and the built CSS has `--primary` equal to indigo `oklch(51.1% .262 276.966)`.
  4. `npm audit` reports 0 vulnerabilities.
- **Commit:** `feat(frontend): add shadcn/ui with uniflow theme`

#### M0.13 — API client and query setup
- **Purpose:** Set up a typed Axios client, the error format, and a React Query provider.
- **Prerequisites:** M0.7, M0.12, M0.12a.
- **Libraries:** Axios `^1.20.0` and TanStack Query `@tanstack/react-query@^5.103.2`, both approved. Also shadcn's `badge` component, added with `npx shadcn@latest add badge`.
- **Files:**
  - `src/shared/api/client.ts`: `api` with a `baseURL` from `VITE_API_URL`, `withCredentials` and `X-Client: web`. A request interceptor adds `Authorization: Bearer` when there is a token.
  - `src/shared/api/errors.ts`: `ApiError`, and `toApiError()`, which handles the error envelope, network errors, responses without an envelope, and anything else thrown
  - `src/shared/api/tokenStore.ts`: an in-memory access token. The refresh logic comes in M1.9.
  - `src/shared/api/health.ts`
  - `src/env.d.ts`: typed `VITE_API_URL`
  - `src/app/queryClient.ts`: `createQueryClient()`, with `staleTime` 30 s, one retry, no retry on 4xx, and no refetch on window focus
  - `src/app/providers.tsx` and `src/app/App.tsx`: wraps the app in `QueryClientProvider`
  - `src/app/dev/HealthBadge.tsx`: `API: checking…`, `ok` or `offline`, shown in `AppLayout` **only when `import.meta.env.DEV`**
  - `src/components/ui/badge.tsx`
  - Tests: `errors.test.ts`, `client.test.ts`, `HealthBadge.test.tsx`, and `routes.test.tsx`, which is updated to use a mocked health call and the query provider
- **Verification:**
  1. `npm test` passes 17 tests, and they pass on repeated runs.
  2. `typecheck` passes and `lint` is clean.
  3. The production build leaves out the badge.
  4. **Manual:** with the backend running, the sidebar badge shows **API: ok**. With the backend stopped, it shows **API: offline**. This also proves CORS works.
- **Commit:** `feat(frontend): add api client and query provider`

#### M0.14 — Frontend CI
- **Purpose:** GitHub runs the frontend checks automatically on every push and pull request.
- **Prerequisites:** M0.11 and M0.13.
- **Files:** `.github/workflows/frontend.yml`
- **Implementation:**
  - Runs on `ubuntu-latest` with Node 24 (LTS) and the npm cache keyed on `frontend/package-lock.json`.
  - Runs `npm ci`, then `lint`, `typecheck`, `test`, `build` and `npm audit --audit-level=high`.
  - Only runs when `frontend/**` or the workflow file changes, and cancels older runs.
  - Checked beforehand: the Windows-generated `package-lock.json` already lists the **Linux** native binaries that Tailwind's oxide, lightningcss, Vite's rolldown and oxlint need.
- **Verification:**
  1. The YAML is valid.
  2. A local rehearsal (`npm ci`, then every step) passes once no dev server holds files in `node_modules`. On Windows, a running `npm run dev` locks Vite's binary and makes `npm ci` fail with EPERM.
  3. Push `main`, and **Actions → Frontend CI** turns green.
- **Commit:** `ci(frontend): add frontend workflow`

#### M0.15 — OpenAPI type generation (**deferred**; reconsider once the frontend foundation works)
- **Purpose:** Generate TypeScript types from the backend's OpenAPI schema.
- **Files:** `frontend/package.json` (a `gen:api` script), `frontend/src/shared/api/schema.d.ts` (generated and committed)
- **Verification:** `npm run gen:api` produces the file, and `typecheck` passes.
- **Commit:** `chore(frontend): generate api types from openapi schema`

---

## M1 — Identity

Unless a task says otherwise, each one depends on the task before it.

| # | Task | Main files | Verify | Commit |
|---|---|---|---|---|
| M1.1 ✅ | School, Programme and Intake models, plus back-office admin, and the shared `core.models.TimeStampedModel` (`created_at`, `updated_at`) | `core/models.py`, `apps/academics/{apps,models,admin}.py`, migration `0001_initial`, `tests/test_models.py`, `INSTALLED_APPS` | Uniqueness tests, and the Programme → School relationship | `feat(academics): add school, programme and intake models` |
| M1.2 ✅ | Reference data read API: `schools/`, `programmes/?school=` and `intakes/`. Active items only, not paginated. No django-filter needed. | `apps/academics/{serializers,views,urls}.py`, `config/api_v1.py`, `tests/test_api.py` | Requires login (403 `permission_denied` until M1.6, then 401), active-only, ordering, the `?school=` filter, and 400 on a bad filter | `feat(academics): add reference data read endpoints` |
| M1.3 ✅ | Seed command that loads **AIU's real structure** from https://aiu.edu.my/academic-programmes/: 3 schools plus the Centre for Foundation and General Studies, and their 23 programmes, with short codes made up by UniFlow because the page shows none. Also sample intakes: AIU has two intakes a year, March and October. | `apps/academics/management/commands/seed_academics.py` (data kept inside the command, no separate fixture file), `tests/test_seed.py` | The command is idempotent (running it twice creates no duplicates) | `chore(academics): add aiu academic structure seed command` |
| M1.4 ✅ | Student and staff profiles, the `create_user` service and `profile_complete` | `apps/accounts/{models,services,admin}.py` | The profile is created with the user, and `profile_complete` is correct for each combination | `feat(accounts): add student and staff profiles` |
| M1.5 ✅ | Djoser registration with the domain rule and activation email | `apps/accounts/{serializers,views,urls,emails}.py`, email templates, `DJOSER` settings | Wrong domain → 400; one activation email sent; activation works; a reused token fails; `set_email` and `DELETE me` return 403 for non-admins | `feat(auth): add registration with email activation` |
| M1.6 ✅ | Login with **Djoser's own URLs** (`djoser.urls.jwt`: create, refresh and verify) and SimpleJWT's `JWTAuthentication`. Simplified at the developer's request: no custom views, no cookie, and the M1.5 `UniFlowUserViewSet` was removed in favour of `djoser.urls`. | `apps/accounts/urls.py`, `config/settings/base.py` (`SIMPLE_JWT`, token blacklist app), `tests/test_jwt.py` | Login returns `{access, refresh}`; the token opens login-only endpoints; wrong or unactivated accounts get 401; refresh rotates | `feat(auth): add jwt login using djoser urls` |
| M1.7 ✅ | Forgot and change password with **Djoser's built-in endpoints** (already in `djoser.urls`): just the retype settings and tests. Old refresh tokens are not cancelled on a password change (they expire in 14 days), which keeps it simple. | `config/settings/base.py`, `tests/test_passwords.py` | The reset email links to the website; unknown emails get the same 204; a link works once; changing needs the current password | `feat(auth): add password reset and change` |
| M1.8 ✅ | "My profile" through Djoser's own `users/me/`: a `MeSerializer` (set as Djoser's `current_user` serializer) with name, role, `profile_complete`, the editable `student_profile` (school, programme, intake, student number) and a read-only `staff_profile`. `capabilities` is added in M2.1. | `apps/accounts/serializers.py`, `config/settings/base.py`, `tests/test_me.py` | Login required; email and role read-only; the programme must belong to the school; inactive choices refused; student number unique; staff can't set a student profile | `feat(accounts): add current user profile endpoint` |
| M1.9 ✅ | Website session: `api/auth.ts`, `context/AuthContext.tsx` (restore on page load, `login`, `logout`), `api/client.ts` (Bearer token, one shared refresh on 401), `components/RequireAuth.tsx`. The access token is in memory; the refresh token is an httpOnly cookie set by the backend's `apps/accounts/cookie_jwt.py`. | `frontend/src/{api,context,components,types}/…`, `router.tsx`, `main.tsx`, `backend/apps/accounts/cookie_jwt.py` | 401 leads to one refresh and a retry; a failed refresh leads to logout; logged-out visitors are sent to `/login?next=`; the session is restored from the cookie | `feat(auth): add frontend session handling` |
| M1.10 ✅ | Login and Register pages: React Hook Form + Zod, shadcn `input`/`label`, a shared `components/FormField.tsx`. Login follows a safe `?next=`; Register checks the `@student.aiu.edu.my` domain and matching passwords, maps backend field errors, and shows "check your email". Logged-in users are redirected away. | `pages/Login/Login.tsx`, `pages/Register/Register.tsx` (+ tests), `components/FormField.tsx`, `api/auth.ts`, `types/auth.ts`, `router.tsx` | Client validation; successful login redirects; 401 is explained; server errors appear under their field; `//evil` next is ignored | `feat(auth): add login and registration pages` |
| M1.11 ✅ | Activate-account page (`/verify-email/:uid/:token`, activates once even under React StrictMode, offers a new link if invalid), forgot-password page, reset-password page (`/reset-password/:uid/:token`), and a "Forgot password?" link on login. All lazy-loaded. | `pages/{ActivateAccount,ForgotPassword,ResetPassword}/…` (+ tests), `api/auth.ts`, `router.tsx`, `pages/Login/Login.tsx` | Activation called once; used link shows "already activated"; invalid link leads to resend; reset needs matching passwords; invalid reset link is explained | `feat(auth): add activation and password reset pages` |
| M1.12 ✅ | Onboarding (`/onboarding`) and Profile (`/profile`) pages. A shared `StudentDetailsForm` (school, then the programme filtered by school, then intake, plus an optional student number). `RequireAuth` sends students with an incomplete profile to onboarding. The profile page has account details, studies, a change-password form and logout; the sidebar has a Profile link and Log out. Uses `api/academics.ts` and `hooks/useAcademics.ts`. | `pages/{Onboarding,Profile}/…` (+ tests), `components/{StudentDetailsForm,SelectField,ChangePasswordForm}.tsx`, `components/{RequireAuth,AppLayout}.tsx`, `api/{academics,auth}.ts`, `hooks/useAcademics.ts`, `types/{academics,auth}.ts`, `router.tsx`, `test/{fixtures,setup}.ts` | Programmes are filtered by school; changing school resets the programme; saving sends the ids and goes Home; incomplete students are redirected; saved studies are pre-filled; password change and logout work | `feat(profile): add onboarding and profile pages` |

## M2 — Permissions, publishing core and staff dashboard shell

| # | Task | Main files | Verify | Commit |
|---|---|---|---|---|
| M2.1 ✅ | `apps/accounts/capabilities.py`: `capabilities_for(user)`, `publishers_for(user)` and the `HasCapability("…")` permission. `users/me/` now includes `capabilities` and `publishers`. | `apps/accounts/{capabilities,serializers}.py`, `tests/test_capabilities.py`, `tests/test_me.py` | Role × capability matrix; school staff without a school get nothing; publishers per role; the permission class; the users/me fields | `feat(accounts): add role-based capabilities` |
| M2.2 | Staff user management API: list, **create staff account** (with a "set your password" email, because only `@student.aiu.edu.my` can self-register), role and school, suspension, `is_staff` sync | `apps/accounts/manage_views.py`, `services.py` | Only super admins; the role change syncs `is_staff` | `feat(accounts): add staff user management endpoints` |
| M2.3 | Reference data management API | `apps/academics/manage_views.py` | Only admins; deactivating hides the item from the read API | `feat(academics): add reference data management endpoints` |
| M2.4 | `Audience` model with 3 fields, its serializer and its summary text | `apps/audiences/*` | Summary text for each combination | `feat(audiences): add audience model` |
| M2.5 | Visibility selectors `visible_audience_q` and `students_matching` | `apps/audiences/selectors.py` | A matrix of 15 or more cases; the two functions agree; no duplicate rows | `feat(audiences): add audience visibility selectors` |
| M2.6 | `PublishableModel` and `TargetedModel`, `published_q`, and the publish and archive services | `apps/publishing/{models,selectors,services}.py` | Constraint violations; expiry boundaries; publishing sets `published_at` | `feat(publishing): add publishable content base` |
| M2.7 | Publisher policy: `manageable_queryset`, `publishers_for`, `can_manage`, `validate_publisher`, and the `CanManageObject` permission | `apps/publishing/policies.py` | Role × publisher × school matrix | `feat(publishing): add publisher policy` |
| M2.8 | Frontend capability helpers, `RequireCapability` and `Can`, capability-driven `StaffLayout` nav, and a staff home placeholder | `shared/auth/*`, `app/layouts/StaffLayout.tsx` | A student gets a 403 page at `/staff`; the nav shows only granted items | `feat(staff): add staff dashboard layout and capability guards` |
| M2.9 | Shared form components: fields, `MarkdownField`, `PublisherSelect`, `AudienceFields`, `SourceLinkFields`, the `Markdown` renderer, `DataTable`, `Dialog` and `Toast` | `shared/forms/*`, `shared/ui/*` | Markdown strips HTML and `javascript:` links; the audience summary is correct | `feat(frontend): add shared form and table components` |
| M2.10 | Staff users page, including a "create staff account" form | `features/staff/users/*` | Only super admins; a role change updates the list | `feat(staff): add user role management page` |
| M2.11 | Staff reference data pages | `features/staff/academics/*` (or `features/academics/staff/*`) | Create, edit and deactivate each type | `feat(staff): add reference data management pages` |

## M3 — Announcements

| # | Task | Verify | Commit |
|---|---|---|---|
| M3.1 | Model and back-office admin | Constraints and indexes | `feat(announcements): add announcement model` |
| M3.2 | Read API: feed, detail and filters (django-filter) | 404 for invisible items; filters; ordering | `feat(announcements): add announcement feed endpoints` |
| M3.3 | Manage API: CRUD, publish and archive | Every role × action; publishing as another school → 403 | `feat(announcements): add announcement management endpoints` |
| M3.4 | Student feed page | Loading, error, empty and data states; filters kept in the URL | `feat(announcements): add announcement feed page` |
| M3.5 | Student detail page | Markdown, source link, expired label | `feat(announcements): add announcement detail page` |
| M3.6 | Staff list page | Status tabs; row actions follow `can_edit` | `feat(staff): add announcements management list` |
| M3.7 | Staff form: create, edit, publish and archive | Validation; server errors shown; a successful publish updates the lists | `feat(staff): add announcement form` |

## M4 — Documents

| # | Task | Verify | Commit |
|---|---|---|---|
| M4.1 | Model and upload checks (`filetype`) | Spoofed type, oversized file and forbidden type are all rejected | `feat(documents): add document model with upload validation` |
| M4.2 | Read API and streamed download | Login required; download headers correct | `feat(documents): add document library and download endpoints` |
| M4.3 | Manage API (multipart) | Scope and capability checks | `feat(documents): add document management endpoints` |
| M4.4 | Announcement attachments (`attachment_ids`) | Only documents the user can manage can be attached | `feat(announcements): support document attachments` |
| M4.5 | Library and detail pages, and `FileLink` | Download through a blob | `feat(documents): add document library pages` |
| M4.6 | Staff documents pages | Upload progress; client-side checks mirror the server | `feat(staff): add document management pages` |
| M4.7 | Attachment field in the announcement form, and attachments on the detail page | Attach and remove | `feat(announcements): add attachments to form and detail` |

## M5 — Events

| # | Task | Verify | Commit |
|---|---|---|---|
| M5.1 | Model and poster (Pillow) | An end time before the start time is rejected | `feat(events): add event model` |
| M5.2 | Read API: list, range and calendar | Events spanning several days overlap the range; the range is capped at 62 days | `feat(events): add event list and calendar endpoints` |
| M5.3 | Manage API | Scope and capability checks | `feat(events): add event management endpoints` |
| M5.4 | List and detail pages | Grouping by date; closed registration hides the button | `feat(events): add events list and detail pages` |
| M5.5 | Calendar view (FullCalendar `daygrid` and `list`) | Changing the visible range fetches with the correct `from` and `to` | `feat(events): add events calendar view` |
| M5.6 | Staff events pages | Poster preview; time validation | `feat(staff): add event management pages` |

## M6 — Communities

| # | Task | Verify | Commit |
|---|---|---|---|
| M6.1 | Models and link host checks | Valid and invalid URLs for each platform | `feat(communities): add community models` |
| M6.2 | Read API and follow | `for_me` and `following` filters; following is idempotent | `feat(communities): add community directory and follow endpoints` |
| M6.3 | Manage API for communities and links | School scope; communities with no school are admin-only | `feat(communities): add community management endpoints` |
| M6.4 | Directory and detail pages, and the follow button | Follow updates instantly and rolls back on error; links have the correct `href` and `rel` | `feat(communities): add community directory pages` |
| M6.5 | Staff communities pages with a link editor | An invalid WhatsApp host is rejected | `feat(staff): add community management pages` |

## M7 — Timetable

| # | Task | Verify | Commit |
|---|---|---|---|
| M7.1 | `Course` and `Term` models and read API | Only one current term | `feat(academics): add course and term models` |
| M7.2 | `Course` and `Term` manage API | Terms are admin-only; school staff manage their own school's courses | `feat(academics): add course and term management endpoints` |
| M7.3 | `CourseSection`, `ClassMeeting` and `SectionEnrollment` models | Constraints; `external_ref` is unique per term | `feat(timetable): add section, meeting and enrolment models` |
| M7.4 | Manage API for sections and nested meetings | School scope; `updated_by` is recorded | `feat(timetable): add timetable management endpoints` |
| M7.5 | Import service that works with any file format (`apply_timetable_rows`, dry run and report) | Create, update and unchanged cases, and errors with row numbers; no adapter yet | `feat(timetable): add timetable import service` |
| M7.6 | Student API: section catalogue and my sections | Only current-term sections can be added | `feat(timetable): add section selection endpoints` |
| M7.7 | Student API: today and week | Around midnight in Kuala Lumpur; outside the term returns empty | `feat(timetable): add today and weekly timetable endpoints` |
| M7.8 | Staff timetable pages: terms, courses, sections and inline meetings | Create, edit and deactivate | `feat(staff): add timetable management pages` |
| M7.9 | Student section picker | Search, add and remove | `feat(timetable): add section picker` |
| M7.10 | Today and week views (FullCalendar `timegrid` for the week) | Empty state links to the section picker | `feat(timetable): add today and weekly timetable views` |
| M7.11 | *Blocked until the university's timetable format is known:* first import adapter and staff import screen | Dry run, review, then apply | `feat(timetable): add <format> timetable import` |

## M8 — Applications and forms

| # | Task | Verify | Commit |
|---|---|---|---|
| M8.1 | Model and derived status | Every status boundary | `feat(applications): add application listing model` |
| M8.2 | Read API | Status filter; default ordering | `feat(applications): add application listing endpoints` |
| M8.3 | Manage API, including supporting documents | Scope and capability checks | `feat(applications): add application management endpoints` |
| M8.4 | List and detail pages | Countdown; closed listings disable the button | `feat(applications): add applications pages` |
| M8.5 | Staff applications pages | Checks that the closing date is after the opening date | `feat(staff): add application management pages` |

## M9 — Notifications

| # | Task | Verify | Commit |
|---|---|---|---|
| M9.1 | Model and API: list, unread count, mark one read, mark all read | Users see only their own notifications | `feat(notifications): add in-app notification endpoints` |
| M9.2 | `notify_audience` called when important announcements and new events are published | Only matching students; publishing twice sends nothing new; normal priority sends nothing | `feat(notifications): notify audience on publish` |
| M9.3 | Bell, notification list page, and targets that link to the item | 60-second polling while the tab is visible; clicking marks the notification read and opens the item | `feat(notifications): add notification bell and list` |
| M9.4 | System broadcast: super admin API and a small staff form | Every active user gets one | `feat(notifications): add system broadcast` |

## M10 — Dashboard, search and release

| # | Task | Verify | Commit |
|---|---|---|---|
| M10.1 | Dashboard API | 15 queries or fewer; visibility is the same as in the lists | `feat(dashboard): add dashboard endpoint` |
| M10.2 | Student dashboard page | Each section has its own empty state | `feat(dashboard): add student dashboard page` |
| M10.3 | Global search API | Items the user cannot see never appear | `feat(search): add global search endpoint` |
| M10.4 | Search page and header search box | 300 ms debounce; a message for queries that are too short | `feat(search): add search page` |
| M10.5 | Staff home: shortcuts and "my recent drafts" | Shows only granted shortcuts | `feat(staff): add staff home page` |
| M10.6 | Production settings hardening | `check --deploy` is clean | `chore(security): harden production settings` |
| M10.7 | Deployment guide and example nginx and systemd configuration (no Docker) | A staging deployment passes smoke tests | `chore(deploy): add deployment guide and server configs` |

---

## Later backlog

This work is kept documented so the MVP design leaves room for it.

| Area | Items |
|---|---|
| Publishing | Community managers and a `community` publisher type, lecturer publishing to their sections, an approval workflow, scheduled publishing and the cron job it needs |
| Targeting | Course, section, community-follower and semester targeting; document audiences |
| Notifications | Closing and opening reminders, event and timetable change notifications, push via Expo with a `Device` model, email digests, preferences, retention |
| Timetable | Additional import adapters, one-off class exceptions, lecturer edits, ICS export |
| Content | Read tracking, event "interested" markers, ICS export, document versioning |
| Platform | Anonymized self-service account deletion and data export, audit log, S3 storage, image resizing, cursor pagination and `updated_since`, full-text search, end-to-end tests with Playwright, SSO |
| Integrations | Telegram bot inbox and outbound posting (see [08](08-messaging-integrations.md)); WhatsApp Cloud API outbound only, and only if justified |
| Mobile | `packages/shared` extraction and an Expo app for the student side |
