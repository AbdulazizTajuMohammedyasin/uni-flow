# UniFlow Progress

This is the **simple overview** of where UniFlow is. It is updated after every task.
(The detailed plan is [11-roadmap.md](11-roadmap.md). You do not need to read it to follow progress.)

**Now:** M0 (Foundations) is almost done.
**Next up:** M0.13, which connects the website to the backend.

---

## The big picture

| Milestone | In plain words | Status |
|---|---|---|
| **M0** Foundations | Set up the empty backend and website so they run and are checked automatically | 🔄 In progress |
| **M1** Identity | Students can register, log in and fill in their profile | ⏳ Not started |
| **M2** Permissions and staff area | Who is allowed to do what, and the staff dashboard frame | ⏳ |
| **M3** Announcements | Staff post announcements, and students see the ones meant for them | ⏳ |
| **M4** Documents | Upload and download documents, and attach them to announcements | ⏳ |
| **M5** Events | Events list and calendar | ⏳ |
| **M6** Communities | Clubs and groups with WhatsApp and Telegram links | ⏳ |
| **M7** Timetable | Students see today's and this week's classes | ⏳ |
| **M8** Applications and forms | What students can apply for, and until when | ⏳ |
| **M9** Notifications | The bell icon for important news | ⏳ |
| **M10** Dashboard, search and launch | Home page, search, and putting it online | ⏳ |

---

## M0 Foundations: task by task

| Task | What it did (plain words) | What you can see or try | Status |
|---|---|---|---|
| M0.1 | Repository rules: line endings, ignored files | – | ✅ Done |
| M0.2 | Database: you created the `uniflow` MySQL database yourself | MySQL Workbench | ✅ Done |
| M0.3 | Created the empty Django backend | – | ✅ Done |
| M0.4 | Connected Django to MySQL, with passwords in `backend/.env` | `pipenv run python manage.py check` | ✅ Done |
| M0.4a | Switched to Pipenv for Python packages | `pipenv --venv` | ✅ Done |
| M0.5 | Automatic backend tests and code checks (pytest, ruff) | `pipenv run pytest` | ✅ Done |
| M0.6 | User accounts: log in with email, each user has a role | `/django-admin/` | ✅ Done |
| M0.7 | The API "doorway" at `/api/v1/`, with a health check | http://127.0.0.1:8000/api/v1/health/ | ✅ Done |
| M0.8 | GitHub checks the backend automatically on every push (CI) | GitHub → **Actions** tab | ✅ Done |
| M0.9 | Created the empty React website | `npm run dev` → http://localhost:5173 | ✅ Done |
| M0.10 | Styling with Tailwind (colours, fonts) | The styled page | ✅ Done |
| M0.11 | Automatic website tests (Vitest) | `npm test` | ✅ Done |
| M0.12 | Pages and addresses (`/`, `/login`, `/staff`, 404) plus the page frames | Click the menu links. Try a phone-size view. | ✅ Done |
| M0.12a | Added **shadcn/ui** (ready-made buttons, dialogs and so on) with UniFlow's indigo colour. It is used on the 404 page's button. | http://localhost:5173/anything → "Go to home" button | ✅ Done |
| **M0.13** | **Website ↔ backend connection: a small "API: ok" badge** | – | ⏭️ **Next** |
| M0.14 | GitHub checks the website automatically too | – | ⏳ |

---

## Where things are

| I want to... | Look at |
|---|---|
| See what's done and what's next | **This file** |
| Run the backend | [backend/README.md](../backend/README.md) |
| Run the website | [frontend/README.md](../frontend/README.md) |
| Understand the whole design | [docs/README.md](README.md) |

### Website files so far (`frontend/src/`)

| File | Job |
|---|---|
| `main.tsx` | Starting point |
| `app/App.tsx` | Turns the router on |
| `app/routes.tsx` | **The router:** which address shows which page (the plan called this `router.tsx`) |
| `app/navigation.ts` | The menu links |
| `app/layouts/` | Page frames: student, login, staff |
| `app/pages/` | Placeholder, 404 and error pages |
| `components/ui/` | **shadcn** components (Button so far). Add more with `npx shadcn@latest add <name>`. |
| `lib/utils.ts` | shadcn's small helper (`cn`) |
| `shared/ui/` | UniFlow's own small reusable boxes |
| `styles/index.css` | Colours and fonts |

### Backend files so far (`backend/`)

| File or folder | Job |
|---|---|
| `config/settings/` | Settings (dev, test, prod) |
| `config/api_v1.py` | The list of API addresses |
| `apps/accounts/` | User accounts |
| `core/` | Shared API pieces: the error format, paging and the health check |
| `.env` | Your local passwords (never committed) |

---

## Open decisions

- Allowed email domains for registration. This is needed before M1.5.
- The university's timetable format. This is needed before M7.11.
- Hosting. This is needed before M10.7.
