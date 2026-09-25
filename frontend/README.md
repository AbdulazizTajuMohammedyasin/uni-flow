# UniFlow Frontend

The React web app for UniFlow: the student area, plus the staff dashboard later. See [docs/05-frontend.md](../docs/05-frontend.md) for the architecture.

Stack: React + TypeScript + Vite + Tailwind CSS v4. More libraries are added only by the roadmap task that needs them.

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
| `npm test` | Run all tests once (Vitest + React Testing Library, in a simulated browser) |
| `npm run test:watch` | Re-run tests automatically on every save |

## Conventions

- `@/` is an alias for `src/`, for example `import { api } from '@/shared/api/client'`.
- TypeScript runs in `strict` mode.
- **UI components come from shadcn/ui** and live in `src/components/ui/`, for example `import { Button } from '@/components/ui/button'`. Add a new one only when a screen needs it: `npx shadcn@latest add dialog`. UniFlow's own small components live in `src/shared/ui/`.
- **Styling uses Tailwind utility classes** in the components. The global stylesheet is `src/styles/index.css`, which holds the Tailwind import, the shadcn theme (with UniFlow indigo as `primary`), the brand colours (for example `bg-brand-600`) and the base body styles. Add a theme token only when a real screen needs it.
- **Tests** sit next to the code they test, as `*.test.ts(x)`, for example `src/App.test.tsx`. Use React Testing Library queries such as `getByRole` and `getByText`, and test what a user sees, not implementation details.
- **Talking to the backend:** use the shared client `api` from `@/shared/api/client` (never call `fetch` directly), wrap each call in a small typed function (see `@/shared/api/health.ts`), and turn errors into an `ApiError` with `toApiError`. Components load data with TanStack Query (`useQuery`).
- In development, a small **API status badge** (`API: ok` or `API: offline`) shows in the sidebar or the mobile top bar. It is not included in production builds.
- Only `VITE_*` environment variables reach the browser, so never put secrets in `.env`.
