# 11 — Roadmap & Implementation Tasks (M0–M10)

> **Re-planned after M2.8** when the product was redefined as an AI-powered information assistant ([01](01-product.md)). M0–M2 are unchanged and reused. From M3 the order proves the core idea early: academic context first, then messages, then an AI slice that **reads timetables and detects timetable changes** students confirm, then real connectors, then the full personal feed, then a **pilot** with real students operated through the Django admin. React staff pages come after the pilot.

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
| **M0** ✅ | Foundations | An empty Django API and an empty React app, both running locally and in CI |
| **M1** ✅ | Identity | Register, activate, log in, onboard and edit the profile |
| **M2** ✅ | Permissions and publishing core | Capabilities, audience visibility ("who is affected"), the shared content base, the school boundary and the `/staff` layout |
| **M3** | Classes and preferences | Courses, terms, sections and weekly classes; who-is-affected by course, section and semester; the semester worked out from the intake; interests and information types; the timetable page with "add a class" |
| **M4** | Sources and messages | The background job runner; sources, group members, messages and files; paste, chat export, timetable uploads and Google Drive links |
| **M5** | AI v1: timetables | The AI reads shared timetables into classes the student confirms, and detects timetable changes the student confirms; the confidence rule; staff posts as insights |
| **M6** | Connectors | The Telegram bot and the WhatsApp connector; students add groups in the app and UniFlow's number joins them |
| **M7** | AI v2: the personal feed | Every insight kind, direct mentions, duplicate merging, relevance and tiers, the "For you" feed |
| **M8** | Notifications | Alerts inside UniFlow by tier, retractions and the daily digest |
| **M9** | Pilot release | Home and search, privacy notice, Django admin set-up for the operator, production settings, deployment, pilot checklist |
| — | **Pilot with real students** | |
| **M10** | Staff pages (after the pilot) | React pages for sources, insight review, official posts, users and reference data |
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
  - `StaffLayout` has a dark sidebar, a "Back to UniFlow" link and a menu built from the user's capabilities (done in M2.8).
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
  - Runs `npm ci`, then `lint`, `typecheck`, `test`, `build` and `npm audit --audit-level=high --omit=dev` (shipped packages only; changed after M3.8 because the shadcn CLI's dependencies had an advisory with no fix).
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
| M2.2 ✅ | Staff user management API at `manage/users/`: list and search, **create staff account** (with a "set your password" email, because only `@student.aiu.edu.my` can self-register), PATCH role, school and suspension, `is_staff` sync. Suspended users can't log in and their tokens stop working (`authentication.py`). | `apps/accounts/{manage_views,manage_urls,authentication,services,serializers}.py`, `config/api_v1.py`, `tests/test_manage_users.py` | Only super admins; the role change syncs `is_staff`; school staff need a school; no self-demotion; suspension blocks login and existing tokens | `feat(accounts): add staff user management endpoints` |
| M2.3 ✅ | Reference data management API at `manage/academics/schools|programmes|intakes/`: list (incl. inactive), create, edit, switch off. No delete. | `apps/academics/{manage_views,manage_urls,serializers}.py`, `config/api_v1.py`, `tests/test_manage_api.py` | Only admins; deactivating hides the item from the read API | `feat(academics): add reference data management endpoints` |
| M2.4 ✅ | `Audience` model with 3 fields (schools, programmes, intakes), `AudienceSerializer` (active choices only) and `summary()` (e.g. "Computing · Intake October 2024"; empty = "All students") | `apps/audiences/{apps,models,serializers}.py`, migration, `config/settings/base.py`, `tests/test_audience.py` | Summary text for each combination | `feat(audiences): add audience model` |
| M2.5 ✅ | Visibility selectors `visible_audience_q(user, via="audience")` and `students_matching(audience)` (active, non-suspended students only) | `apps/audiences/selectors.py`, `tests/test_selectors.py` | A matrix of 15 or more cases; the two functions agree; no duplicate rows | `feat(audiences): add audience visibility selectors` |
| M2.6 ✅ | `PublishableModel` and `TargetedModel` (abstract; no migration), `published_q`, `is_expired`, and the `publish` / `archive` services. Tested through a test-only `SamplePost` model whose table `backend/conftest.py` creates. | `apps/publishing/{apps,models,selectors,services}.py`, `apps/publishing/tests/{models,test_publishing}.py`, `conftest.py`, `config/settings/base.py` | Constraint violations; expiry boundaries; publishing sets `published_at` | `feat(publishing): add publishable content base` |
| M2.7 ✅ | Publisher policy: `manageable_queryset`, `can_manage`, `validate_publisher`, `validate_audience` and the `CanManageObject` permission (`publishers_for` is reused from M2.1) | `apps/publishing/policies.py`, `tests/test_policies.py` | Role × publisher × school matrix | `feat(publishing): add publisher policy` |
| M2.8 ✅ | Frontend capability helpers, `RequireCapability` and `Can`, capability-driven `StaffLayout` nav, a staff home placeholder, a "No access" page and a "Staff dashboard" link for staff | `lib/capabilities.ts`, `components/{RequireCapability,Can,StaffLayout,AppLayout}.tsx`, `pages/NoAccess/`, `lib/navigation.ts`, `router.tsx`, `types/auth.ts` | A student gets a 403 page at `/staff`; the nav shows only granted items | `feat(staff): add staff dashboard layout and capability guards` |
| ~~M2.9~~ | *Moved:* shared form components are built inside the first pages that need them (M3, M5, M10) instead of up front | – | – |
| ~~M2.10~~ | *Moved to M10.5* (staff users page) | – | – |
| ~~M2.11~~ | *Moved to M10.6* (reference data pages) | – | – |

## M3 — Classes and preferences

The AI can only tell who is affected if UniFlow knows each student's classes. Every model gets a Django admin page, which is how the operator fixes data in the pilot.

| # | Task | Verify | Commit |
|---|---|---|---|
| M3.1 ✅ | `Course` and `Term` models (the current term is worked out from the dates, `Term.current`; changed after M3.8), read API `courses/` (`?school=`, `?search=`), `terms/`, `terms/current/`, and Django admin | Only one current term | `feat(academics): add course and term models` |
| M3.2 ✅ | New `timetable` app: `CourseSection` (with `source`), `ClassMeeting` and `SectionEnrollment` models and Django admin (weekly classes edited inside the section) | Constraints; `external_ref` unique per term | `feat(timetable): add section, meeting and enrolment models` |
| M3.3 ✅ | `Audience` gains `courses` (students in a section of the course **this term**) and `sections`; selectors, their test matrix and the school-boundary check (`validate_audience`) extended. Semester targeting moved to M3.4, where the semester is worked out. | The two selectors still agree; no duplicate rows | `feat(audiences): add course and section targeting` |
| M3.4 ✅ | Semester worked out from the intake (counting the official terms that started since the intake; `accounts/semesters.py`; `seed_academics` loads AIU's official 2024/2025 and 2025/2026 terms for both the Undergraduate and Foundation calendars; `Term.calendar`) with `semester_override`; `Audience` gains `semester_min` and `semester_max`; `interests`, `info_types`, `aliases`; `auth/preferences/choices/` | Semester correct for each intake and date; semester targeting in the selector matrix; choices validated | `feat(accounts): add semester and preferences to profile` |
| M3.5 ✅ | Student API: section catalogue (`timetable/sections/`, current term of the student's calendar; `?search=`, `?course=`, `?school=`), my sections (`timetable/my-sections/`), add a class by hand (`POST timetable/sections/`) | A hand-added class creates the course and section once; the caller is enrolled | `feat(timetable): add section selection endpoints` |
| M3.6 ✅ | Student API: `timetable/today/` and `timetable/week/?date=` (the student's sections in the current term; Kuala Lumpur date; empty outside the term) | Around midnight in Kuala Lumpur; outside the term returns empty | `feat(timetable): add today and weekly timetable endpoints` |
| M3.7 ✅ | Onboarding step 2 (interests, information types, nicknames; skippable) and a profile "Your interests" section (`components/PreferencesForm.tsx`, `hooks/usePreferences.ts`); the profile shows the worked-out semester with an optional correction | New students complete every step; edits save | `feat(profile): add preferences to onboarding` |
| M3.8 ✅ | Timetable page (`/timetable`, `?view=week&date=`): today and week as **simple day lists** (no FullCalendar: simpler and easier on phones), "My sections" with search-to-add and remove, and the "add a missing class" form | Empty state offers "Add my timetable" (enabled in M5) and "add a class" | `feat(timetable): add timetable page` |

## M4 — Sources and messages

| # | Task | Verify | Commit |
|---|---|---|---|
| M4.1 ✅ | **Celery with Redis** (changed from a database job table at the developer's request): `config/celery.py`, `CELERY_*` settings, jobs run immediately in tests, and a `ping` job to check the set-up | The worker connects to Redis and `ping` returns `'pong'`; tests need no Redis | `feat(core): add celery background jobs` |
| M4.2 ✅ | New `intelligence` app: `Source` (suggested scope), `SourceMember` and `Message` models with Django admin | `unique(platform, external_id)`; `unique(source, external_id)` | `feat(intelligence): add source and message models` |
| M4.3 ✅ | `POST sources/` (a group for pasted messages), paste messages into a source, and WhatsApp chat-export parsing (`intelligence/whatsapp_export.py`: Android, iPhone and copied-in-app formats; multi-line messages; system lines and media skipped; day/month detection); messages get a fingerprint so nothing is stored twice | Multi-line messages and dates parsed; re-upload stores nothing twice | `feat(intelligence): add message paste and chat export import` |
| M4.4 ✅ | `MessageFile` and `intelligence/files.py`: timetable uploads (image, PDF, XLSX) checked by real contents with `filetype`, 10 MB limit, private storage with random names, and safe Google Drive / Docs link fetching (Google hosts only, every redirect checked). The upload screen comes with M5.5. | Fake types and other hosts refused; private files only for their owner | `feat(intelligence): add message files and drive links` |
| M4.5 ✅ | Retention job (`intelligence/tasks.py`, Celery Beat every night at 03:00): clear raw text and files after `MESSAGE_RETENTION_DAYS` (60) | Old text and files cleared; evidence quotes kept | `feat(intelligence): add message retention` |
| M4.6 ✅ | "Groups" page (`/sources`; replaces the Communities menu item): my groups with message counts, add a group, paste messages, upload a WhatsApp export | Upload progress; errors shown | `feat(intelligence): add sources page` |

## M5 — AI v1: timetables (the proof slice)

**Decided:** Gemini (free tier for now) through `google-genai` ([12](12-intelligence.md#ai-provider)). **Needs approval:** `openpyxl` for spreadsheet timetables (M5.4).

| # | Task | Verify | Commit |
|---|---|---|---|
| M5.1 ✅ | `providers.py`: one `ask_json` interface, `GeminiProvider` (`google-genai`; fast model `gemini-3.1-flash-lite`, smart model `gemini-3.5-flash`), `FakeProvider` for tests, `AIRateLimited` for "too many requests", and `manage.py check_ai`. No spend limit on the free tier. | Tests never call the network; rate limits are recognised | `feat(intelligence): add ai provider interface` |
| M5.2 ✅ | `Insight(TargetedModel)` with publisher type `source` (`publisher_source` on `Insight`), `InsightEvidence` (quote kept after the clean-up), the confidence rule (`CONFIDENT` 0.8, `UNSURE` 0.5, `save_ai_insight`), and staff posts in the Django admin with Publish and Retract actions (`Audience` admin page added) | Confidence below 0.5 → draft; 0.5–0.8 → digest-only and "Not confirmed"; staff posts publish normally | `feat(intelligence): add insight model` |
| M5.3 ✅ | Triage (`intelligence/triage.py`, Celery job `triage_source`, started when new messages are saved; admin action "Sort new messages now"): batches of up to 30 new messages → `noise` or `relevant` with the fast model; files → relevant and empty text → noise without the AI; "too many requests" → retry after 1, 2, 4… minutes. Checked against the real Gemini with sample messages, including a prompt-injection attempt. | Noise stops the pipeline | `feat(intelligence): add message triage` |
| M5.4 ✅ | Reading timetables (`intelligence/timetable_reading.py`, Celery job `read_timetable_import`; `TimetableImport` lives in `intelligence`; `openpyxl`): the AI reads an image, PDF or spreadsheet into rows (a spreadsheet tab by tab, **once per file**, stored on `MessageFile.reading`; each student gets the tab matching their programme and intake); confirm applies them with the import service (never overwriting existing classes) | Nothing saved before confirm; confirm creates missing classes and enrols | `feat(timetable): read timetables with ai` |
| M5.5 ✅ | Timetable imports API (`timetable/imports/`, `intelligence/timetable_urls.py`) and "Add my timetable" on the Timetable page (upload or link, reading status, tab switch, untick classes, confirm or "Not my timetable"); AIU-only links explain how to download and upload instead | Editing a row before confirm is respected | `feat(timetable): add timetable import page` |
| M5.6 ✅ | Change extraction for the four timetable kinds with the conversation window; resolve course, section and date to a class (`intelligence/extraction.py`, job `extract_source` runs after triage finds academic messages; `Message.extracted_at`) | Unknown course → draft for review; invalid output rejected | `feat(intelligence): detect timetable changes` |
| M5.7 ✅ | `ClassChange` (one per insight and section, in `timetable`) and `ClassChangeConfirmation` (saved when the student answers); `timetable/changes.py` (propose, retract, decide, apply); `publish_insight` / `retract_insight` in intelligence services and the admin actions; confirm and reject API; today and week include confirmed changes and flag pending ones; retraction; the AI step also gives `new_date` for a class moved to another day | A student sees only their own confirmed changes | `feat(timetable): add student-confirmed class changes` |
| M5.8 ✅ | Timetable page: pending-change banner with evidence, Confirm and Reject, changed markers (`components/ClassChanges.tsx`; labels "Moved", "Cancelled", "Room changed", "Extra class", "Change waiting"; a confirmed cancelled class is crossed out) | Confirming updates the week view | `feat(timetable): add change confirmation to timetable page` |
| M5.9 ✅ | Evaluation set (`apps/intelligence/tests/eval/`: 15 conversations, 2 timetable sheets) and `manage.py evaluate_intelligence [--only changes|timetables]` (timetable reading and changes; nothing saved; retries when the AI is busy) | Prints accuracy per kind | `test(intelligence): add evaluation command and dataset` |

## M6 — Connectors

**Needs approval first:** the WhatsApp connector library and a dedicated number ([08](08-messaging-integrations.md#how-it-is-built)).

| # | Task | Verify | Commit |
|---|---|---|---|
| M6.1 ✅ | Telegram webhook: group and channel messages and their files; `setWebhook` command (`intelligence/telegram.py`, `TelegramWebhookView`, task `fetch_telegram_file`, `manage.py set_telegram_webhook <https://site> | --info | --delete`; the bot added or removed sets the source active or disconnected; supergroup upgrades keep the source; Python's urllib, no new library) | Wrong secret → 403; duplicates stored once | `feat(intelligence): add telegram bot webhook` |
| M6.2 ✅ | Internal connector API: messages, files, pending invites, joined; signed requests (`intelligence/connector.py`, `internal_urls.py`; HMAC-SHA256 of `timestamp.METHOD.path.body` with `CONNECTOR_SECRET`, 5 minutes; the sender id is hashed again on UniFlow's side; a second link to a group already joined merges into it) | Bad signature → 403; old timestamp rejected | `feat(intelligence): add internal connector endpoints` |
| M6.3 🔄 | The WhatsApp connector process (`connectors/whatsapp/`): join by invite (or wait for admin approval), join notice, messages and files (Node.js 24 + **Baileys 7.0.0-rc14**, approved; pairing-code login; one join per round, each link at most hourly; current WhatsApp Web version fetched at start; `node --test` and its own CI workflow). **Built; the real test waits for the dedicated number, and linking may need a Baileys patch** (`companion_reg_refresh`, Baileys #2737) | Manual test on a test group; a restart resumes without duplicates | `feat(connectors): add whatsapp connector` |
| M6.4 ✅ | Add-a-group API and page (invite link, suggested scope, joining an already-connected group, pending state) (`POST sources/connect/`, `services.whatsapp_invite` / `connect_group`; the Groups page has one "Add a group" form: name + optional WhatsApp link; Telegram links explain how to add the bot; scope pickers in the page are left for later, the API accepts them) | Already-connected groups are not joined twice; wrong hosts refused | `feat(intelligence): add a group flow` |
| M6.5 ✅ | A timetable shared in a group creates a ready import for each member without classes (`timetable_reading.offer_to_group`, task `offer_group_timetable`, started when a Telegram or connector file is saved; the AI reads the file only if a member needs it; no classes → ignored; imports show `group`; `GroupTimetableOffer` on the Timetable page) | Members get "Is this your timetable?"; others don't | `feat(timetable): offer group timetables to members` |

## M7 — AI v2: the personal feed

| # | Task | Verify | Commit |
|---|---|---|---|
| M7.1 ✅ | Extraction for every kind (opportunities, notices, `direct_request`) with importance, action, info type, topics and dates (same single AI request as timetable changes: `changes` + `items`, prompt `extract-v2`; `check_item`, `item_audience` (codes UniFlow knows and a semester range, else the group's scope), `save_item`; the replied-to message is added to the window; names kept in `data` for M7.2; checked once on the real Gemini) | Each kind extracted from sample messages via the fake provider | `feat(intelligence): extract all insight kinds` |
| M7.2 ✅ | Direct mentions: among the students who added the group first, full names and nicknames (`intelligence/mentions.py`, `InsightMention`; then the students the group is for, never all students; part of a name and titles like "Bro" handled; recorded when a `direct_request` is saved; shown on the insight in the admin) | A name shared by two members is not a mention | `feat(intelligence): detect direct student mentions` |
| M7.3 ✅ | Duplicate merging (`merge_key`, extra evidence) (`intelligence/merging.py`: last 14 days, same kind; timetable changes only on the exact key incl. new time/room; others on the same link, or the same date and a similar title; the higher confidence wins and can publish an unsure draft; a copy's link is adopted) | A forwarded copy adds evidence, not a new insight | `feat(intelligence): merge duplicate insights` |
| M7.4 ✅ | `Delivery`: relevance (including group membership), tiers and reasons (`intelligence/delivery.py`; run on publish, after mentions and after a merged copy; never undoes read/dismissed; read-only admin page) | The relevance and tier matrix | `feat(intelligence): add per-student relevance and tiers` |
| M7.5 ✅ | Feed API: list by tier, detail with evidence, read, dismiss, "not relevant" (`intelligence/feed.py`, `feed_urls.py`; paginated; Telegram messages link to the post, WhatsApp to the group; a timetable change shows my answer; home and search come later) | Only the caller's deliveries; 404 otherwise | `feat(intelligence): add personal feed endpoints` |
| M7.6 ✅ | "For you" page and insight detail page; the student menu becomes For you, Timetable, Sources, Notifications, Profile (`pages/ForYou`, `pages/Insight`; menu now For you, Timetable, Groups, with Profile in the sidebar footer as before; **Notifications is added with M8**, so the menu never links to an empty page; opening an item marks it read) | Four tiers in order; evidence and "open original"; old menu items gone | `feat(intelligence): add for you and insight pages` |

## M8 — Notifications (inside UniFlow)

| # | Task | Verify | Commit |
|---|---|---|---|
| M8.1 ✅ | `Notification` model and API: list, unread count, mark read, mark all read (new app `apps/notifications`; `dedupe_key` never sends the same alert twice; read-only admin; kinds named for the API docs: `NotificationKind`, and `ClassChangeKind` moved out of `ClassChange` for the same reason) | Users see only their own | `feat(notifications): add in-app notification endpoints` |
| M8.2 ✅ | `notify_deliveries`: immediate tiers, timetable proposals and retractions (in `intelligence/delivery.py`, so `notifications` doesn't depend on `intelligence`; `notifications.services.send` stores alerts; Celery tasks `notify_insight` and `notify_retraction` after commit; `Delivery.notified_at` claims each delivery) | Only immediate tiers notify; merged duplicates notify nobody; never twice | `feat(notifications): notify students by tier` |
| M8.3 ✅ | Daily digest job and digest page (`delivery.send_daily_digests`, Celery Beat `send-daily-digest` at 19:00; `GET feed/digest/?date=`; feed items now include `info_type`; `pages/Digest` grouped by type) | One digest per student per day, only if there is something new | `feat(notifications): add daily digest` |
| M8.4 ✅ | Bell, notification list and links to the insight (`pages/Notifications`; "Notifications" in the menu with the unread count, polled every 60 s only while the tab is visible; an insight alert opens `/insights/:id`, the digest alert `/digest?date=`; mark all as read) | 60-second polling while the tab is visible | `feat(notifications): add notification bell and list` |

## M9 — Pilot release

| # | Task | Verify | Commit |
|---|---|---|---|
| M9.1 ✅ | Home API and page: direct, action, important, today's classes, pending changes (`GET feed/home/`, `feed.home()`; the For you page gets a "Today" box (`components/TodayBox.tsx`) instead of a separate page; staff get empty classes and changes) | Same visibility as the feed; 15 queries or fewer | `feat(intelligence): add home screen` |
| M9.2 ✅ | Search API and page over the caller's deliveries (`feed.search()`, `GET feed/search/?q=`; every word must match the title, summary, place, action or a quoted message; read, dismissed and digested items included; `pages/Search`, "Search" in the menu; the For you card became the shared `FeedItemCard`) | Never returns undelivered insights | `feat(intelligence): add search` |
| M9.3 ✅ | Privacy notice (registration and profile) and the sender exclusion list (public page `/privacy` linked from registration and the profile; `ExcludedSender` + `services.exclude_sender` (erases stored text and quotes) + the admin action on Messages; skipped in paste, export, Telegram and the connector) | Excluded senders' messages are skipped | `feat(accounts): add privacy notice and sender exclusion` |
| M9.4 | Django admin for the operator: draft queue, publish and retract actions, source review, AI usage list | Actions do the same as the services | `feat(intelligence): add operator admin actions` |
| M9.5 | Production settings hardening | `check --deploy` is clean | `chore(security): harden production settings` |
| M9.6 | Deployment guide: nginx, gunicorn, Redis, the Celery worker and Beat, and the WhatsApp connector as systemd services; `internal/` blocked | A staging deployment passes smoke tests | `chore(deploy): add deployment guide and server configs` |
| M9.7 | Pilot checklist: university approval, WhatsApp number, Telegram bot, Gemini paid tier (privacy) and a spend limit, the pilot intake and groups | Checklist signed off | `docs(release): add pilot checklist` |

## M10 — Staff pages (after the pilot)

Built in the order the pilot shows is needed.

| # | Task | Verify | Commit |
|---|---|---|---|
| M10.1 | Capabilities `sources.manage` and `insights.review`; the four unused capabilities and their staff menu items removed | `me.capabilities` and the staff menu match the new list | `refactor(accounts): update capabilities for sources and insights` |
| M10.2 | Staff sources page (review, scope, disconnect) | School staff only see their school's sources | `feat(staff): add source management` |
| M10.3 | Insight review page: drafts first, correct or retract | A retraction notifies affected students | `feat(staff): add insight review` |
| M10.4 | Official post form (`origin = staff` insights) | The school boundary (M2.7) applies | `feat(staff): add official post form` |
| M10.5 | Staff users page, including "create staff account" (was M2.10) | Only super admins | `feat(staff): add user management page` |
| M10.6 | Staff reference data pages (was M2.11) | Create, edit and deactivate | `feat(staff): add reference data pages` |
| M10.7 | AI usage page | Admins only | `feat(staff): add ai usage page` |

---

## Later backlog

| Area | Items |
|---|---|
| Notifications | Push via Expo with a `Device` model (with the mobile app), email digests, per-tier preferences and quiet hours, deadline reminders |
| Intelligence | Learning from "not relevant" feedback, "what did I miss?" summaries, attachments and images from messages (posters, PDFs), voice notes |
| Timetable | "Connect your Google account" to read AIU-only Drive links (Google app review), adapters for the university's own timetable export, class representatives or lecturers confirming changes for a whole section, ICS export |
| Directories | Browsable announcements, documents, events (with calendar), applications and communities |
| Publishing | Community managers, lecturer posts to their sections, scheduled posts |
| Platform | Anonymized self-service account deletion and data export, audit log, S3 storage, full-text search, end-to-end tests with Playwright, SSO |
| Mobile | `packages/shared` extraction and an Expo app for students |
