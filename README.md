# UniFlow

UniFlow is an **AI-powered student information assistant**. It processes the university's academic WhatsApp and Telegram groups, understands what matters to each student, and brings only that into one personalized place: timetable changes, class cancellations, internships, mandatory events, notices, and messages that mention them by name.

> "No fluff. No information overload. Just the information that matters to you."

Students keep talking in WhatsApp and Telegram. UniFlow removes the need to monitor dozens of groups every day. See [docs/01-product.md](docs/01-product.md).

## Screenshots

**For you**: what needs the student's attention, today's classes, and the updates that affect them.

![The For you page: items that need attention, today's classes and important updates](docs/screenshots/for-you.png)

<table>
  <tr>
    <td width="50%"><img src="docs/screenshots/announcement.png" alt="An announcement about a moved class, with the original group message it came from"></td>
    <td width="50%"><img src="docs/screenshots/timetable-week.png" alt="The weekly timetable, with a room change and a class change waiting for confirmation"></td>
  </tr>
  <tr>
    <td><b>Announcement</b>: why the student sees it, and the group message it came from.</td>
    <td><b>Timetable</b>: the week at a glance; class changes found in group messages wait for the student to confirm.</td>
  </tr>
  <tr>
    <td><img src="docs/screenshots/groups.png" alt="The Groups page, listing connected WhatsApp and Telegram groups"></td>
    <td><img src="docs/screenshots/search.png" alt="Searching the student's items for an internship"></td>
  </tr>
  <tr>
    <td><b>Groups</b>: connect a WhatsApp group by invite link or by adding UniFlow's number, or paste messages.</td>
    <td><b>Search</b>: find anything UniFlow has picked out for the student.</td>
  </tr>
  <tr>
    <td colspan="2"><img src="docs/screenshots/notifications-dark.png" alt="Notifications in dark mode, filtered to the ones that need the student"></td>
  </tr>
  <tr>
    <td colspan="2"><b>Notifications</b>, in dark mode: the ones that need the student are one tap away.</td>
  </tr>
</table>

**On a phone**

<p>
  <img src="docs/screenshots/phone-for-you.png" alt="The For you page on a phone" width="260">
  <img src="docs/screenshots/phone-timetable.png" alt="Today's classes on a phone, with a class change to confirm" width="260">
  <img src="docs/screenshots/phone-announcement-dark.png" alt="An announcement on a phone in dark mode" width="260">
</p>

<sub>The screenshots use made-up sample data: no real students, staff or messages. Regenerate them with <code>npm run screens:readme</code> in <code>frontend/</code>.</sub>

## Status

Milestones M0–M8 are built: accounts and roles, courses and timetables, message intake from WhatsApp, Telegram, pasted text and chat exports, the AI pipeline, the personal "For you" feed and in-app notifications. M9, the pilot release, is in progress: search, the privacy notice, the public home page, push notifications through Expo and the production setup are built; deployment and the pilot with real students are next. Staff pages (M10) come after the pilot; until then the Django admin is the operator's tool. See [docs/PROGRESS.md](docs/PROGRESS.md).

## Repository layout

```
UniFlow/
├── frontend/             React + TypeScript + Vite: public home page, student area, staff dashboard frame
├── backend/              Django + Django REST Framework API (modular monolith)
├── connectors/whatsapp/  Node.js process that runs UniFlow's WhatsApp number (Baileys)
├── deploy/               Docker Compose file to run the production images locally
├── docs/                 Product, architecture, API, deployment and roadmap
├── .github/workflows/    CI for the backend, frontend and connector
└── README.md
```

## Stack

- **Backend:** Python 3.13, Django 5.2 LTS, Django REST Framework, Djoser for accounts, SimpleJWT for tokens (refresh token in an httpOnly cookie), drf-spectacular for the OpenAPI schema
- **Database:** MySQL 8.4 for local development; PostgreSQL in production (Supabase). CI runs the backend tests on both.
- **Background jobs:** [Inngest](https://www.inngest.com/), which calls Django at `/api/inngest`. No worker process and no Redis.
- **AI:** Google Gemini through the `google-genai` SDK, behind a single provider module (`backend/apps/intelligence/providers.py`) with model fallback
- **Sources:** an official Telegram bot (webhook), a WhatsApp connector built on Baileys, and manual paste or chat export as a fallback
- **Web:** React 19, TypeScript, Vite, React Router, TanStack Query, Axios, Tailwind CSS v4, shadcn/ui (Radix), React Hook Form, Zod
- **Testing:** pytest and pytest-django; Vitest and React Testing Library; Playwright smoke, accessibility and screenshot tests; Ruff and oxlint
- **Hosting:** the website on Vercel, the API on Render from a Docker image, files in Supabase Storage, email through Brevo. Docker is used only for deployment, not for local development. See [docs/deployment.md](docs/deployment.md).
- **Mobile:** a React Native (Expo) app, kept outside this repository, runs the website and receives push notifications that the backend sends through Expo's push service. A fully native app on the same `/api/v1/` API comes later.

## Getting started

### Prerequisites

| Tool | Version | Notes |
|---|---|---|
| Git | recent | Line endings are normalized to LF by `.gitattributes` |
| Python | 3.13 | Backend |
| Pipenv | recent | Backend dependency management (`Pipfile` / `Pipfile.lock`) |
| Node.js | current LTS | Frontend |
| MySQL | 8.4 (any 8.x works) | Native local install for development (Docker is only used to run UniFlow online: `deploy/`) |
| Editor | any with [EditorConfig](https://editorconfig.org) support | Picks up `.editorconfig` automatically (VS Code needs the EditorConfig extension) |

### Setup

1. Clone the repository.
2. Create a local MySQL database named `uniflow` (see [docs/development-setup.md](docs/development-setup.md#1-local-database)).
3. Backend: see [backend/README.md](backend/README.md), including the Inngest dev server that runs background jobs locally.
4. Frontend: see [frontend/README.md](frontend/README.md).
5. WhatsApp connector (optional): see [connectors/whatsapp/README.md](connectors/whatsapp/README.md).

### Repository conventions

- **Configuration is scoped.** The root holds only repository-wide files: `.gitattributes`, `.editorconfig`, a `.gitignore` for OS and editor files, and `.github/`. Backend-specific configuration and ignores live in `backend/`, and frontend-specific ones in `frontend/`.
- **Line endings:** LF in the repository for all text files, except Windows `.bat` and `.cmd` scripts.
- **Indentation:** 4 spaces for Python, 2 spaces for everything else.
- **Workflow:** one small task per commit, committed directly on `main`, using [Conventional Commits](https://www.conventionalcommits.org/). See [docs/11-roadmap.md](docs/11-roadmap.md#development-workflow).

## Documentation

Start with [docs/README.md](docs/README.md). The development workflow and task list are in [docs/11-roadmap.md](docs/11-roadmap.md).
