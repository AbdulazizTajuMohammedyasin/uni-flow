# UniFlow Documentation

Status: **The architecture has been reviewed and updated. Implementation waits for approval.** No application code exists yet.

Throughout these docs, **[MVP]** means the item is built in milestones M0–M10. **[Later]** means it is designed and documented but not built yet.

> **Want the simple version?** [PROGRESS.md](PROGRESS.md) shows, in plain words, what is done, what is next, and where each file is.

## Reading order

| # | Document | Covers |
|---|---|---|
| 01 | [Product definition](01-product.md) | Product, MVP / Later / out-of-scope, roles, feature breakdown |
| 02 | [System & backend architecture](02-system-architecture.md) | System architecture, the read and manage API surfaces, Django apps, libraries, environment, MySQL, files |
| 03 | [Data model](03-data-model.md) | Entities, constraints, audience targeting, the timetable data flow |
| 04 | [REST API](04-api.md) | Auth (Djoser and SimpleJWT), the read surface, the manage surface |
| 05 | [Frontend](05-frontend.md) | The React student area, the staff dashboard, and future React Native |
| 06 | [Auth & permissions](06-auth-and-permissions.md) | Djoser configuration, JWT, how roles map to capabilities and scope |
| 07 | [Notifications](07-notifications.md) | In-app notifications on publish, and what comes later |
| 08 | [Messaging integrations](08-messaging-integrations.md) | What WhatsApp and Telegram officially allow; links in the MVP, Telegram bot later |
| 09 | [Security](09-security.md) | Threats and controls |
| 10 | [Testing & deployment](10-testing-and-deployment.md) | Test layers, CI, deployment without Docker |
| 11 | [Roadmap](11-roadmap.md) | **The development workflow**, milestones M0–M10, task cards, the Later backlog |

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
└── frontend/             # React app — owns its own .gitignore, .env.example, package.json, oxlint/tsconfig/vite config
```

- Settings that apply to only one side of the project live inside `backend/` or `frontend/`.
- **There are no Docker files**, and no `mobile/` or `packages/` folders until the React Native work is approved.

## Key architecture decisions

| # | Decision |
|---|---|
| D1 | A modular Django monolith. Each app is split into selectors (reads), services (writes) and policies (permissions). |
| D2 | One versioned API at `/api/v1/` for web now and mobile later. It has two surfaces: **read** (`/api/v1/<resource>/`) and **manage** (`/api/v1/manage/<resource>/`). |
| D3 | **A React staff dashboard (`/staff`) is the staff interface.** The Django admin (`/django-admin/`) is a back-office tool for developers and super admins only. |
| D4 | **The frontend is not a security boundary.** Roles map to *capabilities*, and a department scope limits what each user can manage. The same functions drive both the API's permission checks and the `me.capabilities` field that the UI uses to hide actions. |
| D5 | MVP publishers are `university_admin` (content across all departments, sent to any audience) and `department_staff` (only content that belongs to and is targeted within their own department; wider reach needs an explicit grant from a university admin, which comes later). Lecturers are read-only. Community managers come later. |
| D6 | A single `Audience` model per item. The MVP targets all students, departments, programmes or intakes. Course, section, follower and semester targeting are designed but come later. |
| D7 | Publishing takes effect immediately, with an optional expiry. There is no scheduling, cron, queue or Redis in the MVP. |
| D8 | Djoser handles the account lifecycle and SimpleJWT handles tokens. The web refresh token is an httpOnly cookie, and mobile will keep it in SecureStore. `is_active` means the email is verified, and suspension is a separate `is_suspended` flag. |
| D9 | Every file is a `Document`, stored locally and streamed only to logged-in users. Documents have no audience in the MVP. |
| D10 | The timetable is **supplied by the university and maintained by staff**. An import service accepts rows in a common structure, so the university's actual file format only affects one small adapter, written once the format is known. Students only choose their sections. |
| D11 | Integrations use official channels only. The MVP has deep links, the original source link, and manual publishing. |
| D12 | Native MySQL 8.4 with no Docker. Local-day logic (such as "today in Kuala Lumpur") is computed in Python, so MySQL's time zone tables are never needed. |
| D13 | Libraries are added only in the task that needs them, and only once approved. |
| D14 | **shadcn/ui** (Radix-based, preset "nova") provides the UI components, themed with UniFlow indigo as the primary colour. Components live in `src/components/ui/` and UniFlow's own small components live in `src/shared/ui/`. |

## Remaining decisions (see the summary in the latest review)

1. Which email domains may register? **This blocks M1.5.**
2. The official name of the level above Department (School or Faculty), if UniFlow ever needs to model it. It is not modelled for now.
3. The university's timetable format. **This blocks only M7.11.**
4. Hosting. **This blocks only M10.7.**
5. Deferred libraries, to be decided when their task arrives:
   - `factory_boy`
   - `filetype` (M4.1)
   - Pillow (M5.1)
   - `openapi-typescript` (M0.15)
   - `whitenoise` (M10.7)

### Resolved

- **Supporting libraries:** approved are `pytest`, `pytest-django`, `ruff`, `django-cors-headers`, `drf-spectacular`, `django-filter`, Vitest and React Testing Library. `django-environ` is rejected in favour of a small `config/env.py` helper that uses only the standard library.
- **Terminology:** a Programme is the degree, a Course is a subject or module (for example CDE2313), and a Department is an academic department.
- **Department staff** manage only content that belongs to and is targeted within their own department.
- **CI:** a MySQL service container in GitHub Actions is acceptable. Local development has no Docker.
