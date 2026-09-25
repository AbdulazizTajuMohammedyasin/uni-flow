# UniFlow Frontend

The React web app for UniFlow: the student area, plus the staff dashboard later. See [docs/05-frontend.md](../docs/05-frontend.md) for the architecture.

Stack: React + TypeScript + Vite. More libraries are added only by the roadmap task that needs them.

## Setup (Windows, PowerShell)

Requires Node.js (current LTS). Run these commands from the `frontend/` folder:

```powershell
npm install
Copy-Item .env.example .env      # VITE_API_URL points to the Django API
npm run dev                      # opens on http://localhost:5173
```

## Scripts

| Command | What it does |
|---|---|
| `npm run dev` | Start the development server with hot reload |
| `npm run build` | Type-check, then build the production files into `dist/` |
| `npm run preview` | Serve the production build locally |
| `npm run lint` | Lint with oxlint (the linter that ships with the Vite template) |
| `npm run typecheck` | TypeScript type check only |

## Conventions

- `@/` is an alias for `src/`, for example `import { api } from '@/shared/api/client'`.
- TypeScript runs in `strict` mode.
- Only `VITE_*` environment variables reach the browser, so never put secrets in `.env`.
