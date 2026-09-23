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

## Documentation

Start with [docs/README.md](docs/README.md). The development workflow and task list are in [docs/11-roadmap.md](docs/11-roadmap.md).
