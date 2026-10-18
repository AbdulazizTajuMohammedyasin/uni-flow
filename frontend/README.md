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
| `npm run e2e` | Browser smoke tests (Playwright, in your installed Chrome): every page loads with no errors and no sideways scrolling at 360–1440 px. A fake backend (`e2e/mock-api.ts`) answers with made-up data, so Django doesn't need to run. It also runs the accessibility checks (`e2e/a11y.spec.ts`): one h1 and one main per page, every control named, a keyboard walk with visible focus on each page, the skip link, reduced motion, and colour contrast of both themes. |
| `npm run screens` | Full-page screenshots of every page and state, phone and desktop, light and dark, into `artifacts/ui/latest/` (git-ignored). Set `SCREENS_RUN=iteration-01` to keep a named set. |

## Conventions

- `@/` is an alias for `src/`, for example `import { api } from '@/api/client'`.
- **Folder layout:** `api/` holds backend calls, one file per area. `components/` holds layouts and shared pieces, with shadcn in `components/ui/`. `context/` holds React contexts such as auth. `hooks/` holds React Query hooks, `useX.ts`. `lib/` holds helpers. `pages/<Name>/<Name>.tsx` holds one folder per page. `types/` holds TypeScript types. `router.tsx` holds the routes.
- TypeScript runs in `strict` mode.
- **UI components come from shadcn/ui** and live in `src/components/ui/`, for example `import { Button } from '@/components/ui/button'`. Add a new one only when a screen needs it: `npx shadcn@latest add dialog`. UniFlow's own small components live in `src/shared/ui/`.
- **Colours come from the theme tokens only** (`bg-card`, `text-muted-foreground`, `bg-attention`, `text-success`, …, defined in `src/index.css` for light and dark). Never use raw palette classes such as `text-slate-600`: they don't switch with dark mode. Light / Dark / System is chosen on the Profile page (`components/ThemeToggle.tsx`).
- **Styling uses Tailwind utility classes** in the components. The global stylesheet is `src/index.css`, which holds the Tailwind import, UniFlow's light and dark theme tokens (deep blue `primary`, amber `attention` for "needs you", `success`, …) and the base body styles. Add a theme token only when a real screen needs it.
- **Tests** sit next to the code they test, as `*.test.ts(x)`, for example `src/App.test.tsx`. Use React Testing Library queries such as `getByRole` and `getByText`, and test what a user sees, not implementation details.
- **Talking to the backend:** use the shared client `api` from `@/api/client` (never call `fetch` directly), add a small typed function to `src/api/<area>.ts` (see `api/health.ts`), and wrap it in a hook in `src/hooks/useX.ts` (see `hooks/useHealth.ts`). Errors become an `ApiError` via `toApiError`.
- **Login:** `context/AuthContext.tsx` provides `useAuth()` (`user`, `login`, `logout`). The access token stays **in memory**, and the refresh token is a secure **httpOnly cookie** set by the backend, so no login data is saved in `localStorage` (only the light/dark choice, `uniflow-theme`). Wrap login-only routes in `components/RequireAuth.tsx`.
- In development, a small **API status badge** (`API: ok` or `API: offline`) shows in the sidebar or the mobile top bar. It is not included in production builds.
- Only `VITE_*` environment variables reach the browser, so never put secrets in `.env`.
