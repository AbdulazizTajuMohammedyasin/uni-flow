# 05 — React Web (Student Area + Staff Dashboard) & Future React Native

## 10. React web architecture

One React app contains two areas:

| Area | Routes | Users |
|---|---|---|
| **Student area** | `/` (For you), `/timetable`, `/sources`, `/search`, `/profile`, … | Everyone who is logged in |
| **Staff dashboard** | `/staff/*` | Users with at least one `*.manage` capability |

They share authentication, the API client, the UI components and the build. Splitting them into two apps would duplicate all of that for no benefit.

### Libraries

| Concern | Library | Status |
|---|---|---|
| Build | Vite 8 + React 19 + TypeScript 6 (`strict`) | Approved |
| Routing | React Router v8 (`react-router`, `createBrowserRouter`) | Approved |
| Server state | TanStack Query | Approved |
| HTTP | Axios | Approved |
| Styling | Tailwind CSS | Approved |
| UI components | **shadcn/ui** (preset "nova", built on **Radix**). Components are copied into `src/components/ui/` and added one at a time with `npx shadcn@latest add <name>`, only when a screen needs them. They bring `radix-ui`, `class-variance-authority`, `cn` (shadcn's class-merge helper), `lucide-react` (icons), `tw-animate-css` and `@fontsource-variable/geist` (the font). | Approved (M0.12a) |
| Forms | React Hook Form + Zod (through `@hookform/resolvers`, which connects the two) | Approved |
| Dates | date-fns (formats times in Asia/Kuala_Lumpur) | Approved |
| Markdown | react-markdown (raw HTML turned off) | Approved |
| Calendar | FullCalendar React | Approved but **not used yet**: the timetable shows simple day lists (M3.8). Add it only if a real calendar grid is needed. |
| Lint | **oxlint**. The current Vite template ships oxlint instead of ESLint. It is configured in `.oxlintrc.json`. | Approved as part of the template |
| Tests | Vitest + React Testing Library, with `jsdom` as the test environment | Approved |
| API types | `openapi-typescript` (generates TypeScript types from the OpenAPI schema) | **Deferred.** Reconsider after the frontend foundation works (M0.15). Until then, types are written by hand in each feature's `types.ts`. |
| Not planned | Radix, sonner, MSW, Playwright, Redux or Zustand | Add one only when a real need appears |

Toasts, dialogs and dropdowns come from shadcn (`components/ui/`), added when a screen needs them.

### Folder structure

```
frontend/src/
├── main.tsx            # entry: QueryClientProvider + RouterProvider (+ AuthProvider from M1.9)
├── router.tsx          # createAppRoutes() and the app router
├── index.css           # Tailwind + shadcn theme + UniFlow colours
├── api/                # backend calls, one file per area: client.ts, errors.ts, health.ts, auth.ts (M1.9) ...
├── hooks/              # React Query hooks per area: useHealth.ts, useFeed.ts ...
├── context/            # AuthContext.tsx (M1.9)
├── types/              # TypeScript shapes of API data: health.ts, auth.ts ...
├── components/         # layouts (AppLayout, AuthLayout, StaffLayout) and shared pieces
│   └── ui/             # shadcn components
├── pages/              # one folder per page: Login/Login.tsx, Register/Register.tsx, NotFound/NotFound.tsx ...
│                       # staff pages later: pages/Staff/<Name>/<Name>.tsx
├── lib/                # utils.ts (shadcn cn), queryClient.ts, navigation.ts
└── test/setup.ts
```

Rules:

- API calls live **only** in `api/`. Pages and components use them through `hooks/`.
- `api/*.ts` files contain **plain typed functions with no React code**, so a future React Native app can reuse them.

### Student area [MVP]

The student area is built around **one personal feed**, not separate content sections.

- **For you (`/`)**: four blocks in this order: **Direct attention**, **Action required**, **Important updates**, then **Digest**. Empty blocks are hidden. Today's classes and pending timetable changes appear at the top.
- **Insight card**: title, one-line summary, tier badge, deadline or date if any, the **reason** ("You are in CDE2313 Section A"), and the source ("CDE2313 Sec A · WhatsApp · 9:12"). Actions: open, dismiss, "not relevant".
- **Insight detail (`/insights/:id`)**: the summary, the structured details (date, time, location, link, action), and the **evidence**: the original message(s) with sender, group and time, plus "Open in WhatsApp/Telegram".
- **Timetable (`/timetable`)**: if the student has no classes yet, **"Add my timetable"** (M5.5: `components/TimetableImport.tsx`, also in the My sections box): upload a timetable image, PDF or spreadsheet, or paste a Google Drive link; or confirm a timetable already found in one of their groups. The AI's rows are shown as an editable list ("Is this your timetable?") with **Confirm**. A small "add a class" form is the fallback. Then today and week views as simple lists of days (no calendar library), with previous/next week buttons, and a **My sections** box to choose (search), remove, or add a missing class (M3.8). Pending changes show as a banner with the evidence and **Confirm / Reject** buttons (M5.8: `components/ClassChanges.tsx`); in Today and Week, a changed class has a label ("Moved", "Cancelled", "Room changed", "Extra class", or "Change waiting" when not answered yet) and a confirmed cancelled class is crossed out.
- **Groups (`/sources`, in the menu instead of Communities since M4.6)**: the groups the student added with their message counts, **paste messages** and **upload a WhatsApp export** for each group (M4.6), and **Add a group** (paste the group's invite link, choose what the group is for; UniFlow's number joins it in the background). Also "Paste messages" and "Upload WhatsApp chat export".
- **Onboarding and profile**: onboarding step 1 is school, programme and intake; step 2 (skippable) is interests, information types and optional nicknames ("only used to notice when someone mentions you"). The profile has the same two parts, and shows the semester worked out from the intake with an optional correction (M3.7). "Add my timetable" comes in M5.
- **Notifications (`/notifications`)** and the bell. Alerts are shown inside UniFlow only; phone notifications come with the mobile app.

### Staff dashboard [after the pilot]

> **In the pilot the developer uses the Django admin** for sources, drafts, corrections, timetable data and official posts. The existing `/staff` frame (M2.8) stays; the pages below are built after the pilot.

- **Only capabilities matter.** `GET /auth/users/me/` returns something like `capabilities: {"announcements.manage": true, "timetable.manage": true, "users.manage": false, ...}` plus `publishers: [{type, id, name}]`. The frontend never checks role names.
  - `StaffLayout` builds its side navigation from the capabilities.
  - `<RequireCapability cap="insights.review">` guards each route and shows a 403 page if the capability is missing.
  - `<Can cap=… >` hides buttons.
  - Per-item `can_edit` and `can_publish` flags from the API control the row actions.
- **Security.** Hiding things in the UI is for convenience only. The backend checks every manage request (see [06](06-auth-and-permissions.md)).
- **Standard page pattern** for review lists (sources, insights) and official posts:
  1. A list page: a `DataTable` with status tabs (Draft, Published, Archived), filters, search and pagination.
  2. A form page for create and edit: React Hook Form with Zod, then Save draft, Publish or Archive.
  3. Actions confirmed with a dialog, with the result shown in a toast.
- **Shared form parts:**
  - `PublisherSelect`, with options from `me.publishers`. It is hidden when there is only one option, which is the case for school staff.
  - `AudienceFields`, with multi-selects for school, programme and intake, and a live summary such as "Computing students, 2024-SEP intake". Leaving all of them empty means all students. That option is offered only to university admins. For school staff, the school is preselected and locked, and the programme list is limited to their school. This is only a convenience, because the API enforces the same rule.
  - `MarkdownField`, a textarea with a preview tab rendered by react-markdown.
- **Pages after the pilot (M10):** Sources (review, scope, disconnect), Insights review (drafts first; correct or retract), Official posts (staff insights), Timetable (terms, courses, sections, weekly meetings, edited inline), Users, and Schools & programmes. Documents, events, applications and communities pages are [Later].
- **Staff home** (`/staff`): items waiting for review, recent official posts, and AI usage for admins.

### API layer

```ts
// api/client.ts
export const api = axios.create({ baseURL: import.meta.env.VITE_API_URL, withCredentials: true,
                                  headers: { "X-Client": "web" } });
// request: Authorization: Bearer <tokenStore.access>
// response: on 401 → single-flight POST /auth/jwt/refresh/ → retry once → else logout()
```

- The access token is kept in memory only.
- **Tokens:** the access token is kept **in memory only** (`api/tokenStore.ts`). The refresh token is in a **secure httpOnly cookie** set by the backend, and page scripts never see it. Nothing goes into `localStorage`.
- On page load, `AuthContext` calls `jwt/refresh/` (the browser sends the cookie). If that works it loads `users/me/`; otherwise the visitor is logged out.
- On a 401, `api/client.ts` refreshes once and repeats the request. Several failing requests share one refresh. `components/RequireAuth.tsx` sends visitors who are not logged in to `/login?next=...`.
- `ApiError {code, message, fields}` reads the backend's error format. Forms pass `fields` to React Hook Form's `setError`.

### React Query usage

- Each feature has query key factories, such as `feedKeys`, `timetableKeys` and `manageInsightKeys`.
- Defaults: `staleTime: 30s` and `retry: 1`, with no retries for 4xx errors.
- Mutations invalidate the lists they affect; confirming a timetable change invalidates `timetableKeys` and `feedKeys`.
- The notification count refetches every 60 seconds while the tab is visible.

### Routing

```
/login  /register  /verify-email/:uid/:token  /forgot-password  /reset-password/:uid/:token   (AuthLayout)
/                          For you: the personal feed       (AppLayout, RequireAuth)
/onboarding                profile completion (students with !profile_complete are redirected here)
/insights/:id  /timetable (?view=today|week)  /timetable/sections  /sources  /notifications  /search?q=  /profile
/staff                     staff home                       (StaffLayout, RequireAuth + any capability)
/staff/sources  /staff/insights  /staff/announcements[/new|/:id]  /staff/timetable[...]  /staff/academics[...]  /staff/users
[Later] /announcements  /events  /documents  /applications  /communities  (browsable lists)
```

Routes are lazy-loaded, so the staff dashboard code never downloads for students.

### State, errors and responsiveness

- **Where state lives:** server data in React Query, the session in `AuthProvider`, filters in the URL, form state in React Hook Form, and anything else in `useState`.
- **Every list and detail page** handles four states: loading (skeleton), error (retry), empty (with guidance) and data. A route-level `errorElement` catches crashes, a 403 shows a permission page, and a 404 shows a not-found page.
- **Mobile-first student area:** a bottom nav below `md` and 44 px tap targets. WhatsApp and Telegram links open the native apps.
- **Staff dashboard:** built primarily for desktop, but it must still be usable on a tablet or phone. Tables switch to stacked cards on narrow screens.

## 11. Future React Native architecture [Later]

```
UniFlow/  (later additions, subject to approval then)
├── mobile/            Expo + React Native + TypeScript
└── packages/shared/   api.ts functions, generated types, zod schemas, query keys (moved out of frontend/src)
```

| Concern | Web | Mobile | Shared? |
|---|---|---|---|
| API functions, types, Zod schemas, query hooks | frontend | the same | Yes, moved to `packages/shared` |
| Tokens | Access token in memory, refresh token in an httpOnly cookie | `expo-secure-store`, with `{refresh}` sent in the body | The same endpoints |
| Navigation and UI | React Router, Tailwind | Expo Router, RN components | No |
| Notifications | In-app polling | Expo push through a new `Device` endpoint | The same `Notification` rows |
| Deep links | `/insights/42` | `uniflow://insights/42` | Both built from `(target_type, target_id)` |

The mobile app will cover the student side. Staff management stays on the web.

The backend already supports mobile:

- No endpoint depends on cookies.
- Media URLs are absolute.
- The API is versioned.
- The home screen is a single endpoint (`feed/home/`).
- Notification targets are type and id pairs rather than web URLs.
