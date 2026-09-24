# UniFlow

UniFlow is a student communication and campus-information platform. It brings together the announcements, events, class timetables, student communities, applications and forms, and documents that are currently scattered across WhatsApp groups and channels, Telegram, and university notices.

UniFlow is an **information layer**. It is not an LMS, it is not an assignment or deadline manager, and it does not replace the Student Hub. WhatsApp and Telegram remain the places where students talk, and UniFlow links students to them.

## Repository layout

```
UniFlow/
├── frontend/   React + TypeScript + Vite: student area and staff dashboard (not scaffolded yet)
├── backend/    Django + Django REST Framework API on MySQL (not scaffolded yet)
├── docs/       Architecture, API design and roadmap
└── README.md
```

## Stack

- **Backend:** Python, Django 5.2 LTS, Django REST Framework, MySQL 8.4 (native install), Djoser for accounts, SimpleJWT for tokens
- **Web:** React, TypeScript, Vite, React Router, TanStack Query, Axios, Tailwind CSS, React Hook Form, Zod
- **Mobile (later):** React Native with Expo, using the same `/api/v1/` API

## Getting started

> The backend and frontend are not scaffolded yet. This section grows as each foundation task (M0) lands.

### Prerequisites

| Tool | Version | Notes |
|---|---|---|
| Git | recent | Line endings are normalized to LF by `.gitattributes` |
| Python | 3.12+ | Backend |
| Node.js | current LTS | Frontend |
| MySQL | 8.4 (any 8.x works) | Native local install, **no Docker** |
| Editor | any with [EditorConfig](https://editorconfig.org) support | Picks up `.editorconfig` automatically (VS Code needs the EditorConfig extension) |

### Setup

1. Clone the repository.
2. Create a local MySQL database named `uniflow` (see [docs/development-setup.md](docs/development-setup.md#1-local-database)).
3. Backend setup: added in M0.3–M0.5.
4. Frontend setup: added in M0.9–M0.11.

### Repository conventions

- **Configuration is scoped.** The root holds only repository-wide files: `.gitattributes`, `.editorconfig`, a `.gitignore` for OS and editor files, and `.github/`. Backend-specific configuration and ignores live in `backend/`, and frontend-specific ones in `frontend/`.
- **Line endings:** LF in the repository for all text files, except Windows `.bat` and `.cmd` scripts.
- **Indentation:** 4 spaces for Python, 2 spaces for everything else.
- **Workflow:** one small task per commit, committed directly on `main`, using [Conventional Commits](https://www.conventionalcommits.org/). See [docs/11-roadmap.md](docs/11-roadmap.md#development-workflow).

## Documentation

Start with [docs/README.md](docs/README.md). The development workflow and task list are in [docs/11-roadmap.md](docs/11-roadmap.md).
