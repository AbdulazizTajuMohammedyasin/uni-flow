# 05 — React Web (Student Area + Staff Dashboard) & Future React Native

## 10. React web architecture

One React app contains two areas:

| Area | Routes | Users |
|---|---|---|
| **Student area** | `/`, `/announcements`, `/events`, `/timetable`, … | Everyone who is logged in |
| **Staff dashboard** | `/staff/*` | Users with at least one `*.manage` capability |

They share authentication, the API client, the UI components and the build. Splitting them into two apps would duplicate all of that for no benefit.

### Libraries

| Concern | Library | Status |
|---|---|---|
| Build | Vite 8 + React 19 + TypeScript 6 (`strict`) | Approved |
| Routing | React Router (`createBrowserRouter`) | Approved |
| Server state | TanStack Query | Approved |
| HTTP | Axios | Approved |
| Styling | Tailwind CSS | Approved |
| Forms | React Hook Form + Zod (through `@hookform/resolvers`, which connects the two) | Approved |
| Dates | date-fns (formats times in Asia/Kuala_Lumpur) | Approved |
| Markdown | react-markdown (raw HTML turned off) | Approved |
| Calendar | FullCalendar React: the `daygrid` plugin for the event month view, `timegrid` for the timetable week view, and `list` for small screens | Approved, used only in M5 and M7 |
| Lint | **oxlint**. The current Vite template ships oxlint instead of ESLint. It is configured in `.oxlintrc.json`. | Approved as part of the template |
| Tests | Vitest + React Testing Library, with `jsdom` as the test environment | Approved |
| API types | `openapi-typescript` (generates TypeScript types from the OpenAPI schema) | **Deferred.** Reconsider after the frontend foundation works (M0.15). Until then, types are written by hand in each feature's `types.ts`. |
| Not planned | Radix, sonner, MSW, Playwright, Redux or Zustand | Add one only when a real need appears |

Toasts, dialogs and dropdowns are small in-house components in `shared/ui`.

### Folder structure (organized by feature)

```
frontend/src/
├── app/
│   ├── main.tsx  App.tsx  providers.tsx  router.tsx
│   └── layouts/
│       ├── AuthLayout.tsx        # login/register/etc.
│       ├── AppLayout.tsx         # student area: sidebar (md+) / bottom nav (mobile)
│       └── StaffLayout.tsx       # staff dashboard: capability-driven side nav
├── features/
│   ├── auth/            AuthProvider, RequireAuth, pages
│   ├── profile/         onboarding, profile
│   ├── dashboard/       student dashboard
│   ├── announcements/
│   │   ├── api.ts            # read API functions (framework-agnostic)
│   │   ├── queries.ts        # React Query hooks
│   │   ├── types.ts
│   │   ├── components/  pages/          # student area
│   │   └── staff/                        # staff dashboard pages + manage api
│   │       ├── manageApi.ts  manageQueries.ts  schemas.ts (zod)
│   │       └── pages/ StaffAnnouncementsPage.tsx  AnnouncementFormPage.tsx
│   ├── documents/ events/ communities/ timetable/ applications/   (same shape)
│   ├── notifications/  search/
│   └── staff/           # staff-only features without a student side:
│       ├── home/        # staff landing page
│       └── users/       # role & suspension management (super admin)
├── shared/
│   ├── api/       client.ts (axios + interceptors), tokenStore.ts, errors.ts   (schema.d.ts only if M0.15 is approved)
│   ├── auth/      useCapabilities.ts, RequireCapability.tsx, Can.tsx
│   ├── ui/        Button, Card, Badge, Skeleton, EmptyState, ErrorState, Toast, Dialog, DataTable, Pagination, Markdown ...
│   ├── forms/     TextField, Select, MultiSelect, DateTimeField, FileField, MarkdownField,
│   │              PublisherSelect, AudienceFields, SourceLinkFields
│   └── lib/       dates.ts, format.ts, platformLinks.ts
└── styles/index.css
```

Rules:

- A feature imports from `shared/` and from its own folder. Anything shared across features moves to `shared/`.
- `api.ts` and `manageApi.ts` contain **plain typed functions with no React code**. A future React Native app can reuse them.

### Staff dashboard [MVP]

- **Only capabilities matter.** `GET /auth/users/me/` returns something like `capabilities: {"announcements.manage": true, "timetable.manage": true, "users.manage": false, ...}` plus `publishers: [{type, id, name}]`. The frontend never checks role names.
  - `StaffLayout` builds its side navigation from the capabilities.
  - `<RequireCapability cap="events.manage">` guards each route and shows a 403 page if the capability is missing.
  - `<Can cap=… >` hides buttons.
  - Per-item `can_edit` and `can_publish` flags from the API control the row actions.
- **Security.** Hiding things in the UI is for convenience only. The backend checks every manage request (see [06](06-auth-and-permissions.md)).
- **Standard page pattern** for each content type:
  1. A list page: a `DataTable` with status tabs (Draft, Published, Archived), filters, search and pagination.
  2. A form page for create and edit: React Hook Form with Zod, then Save draft, Publish or Archive.
  3. Actions confirmed with a dialog, with the result shown in a toast.
- **Shared form parts:**
  - `PublisherSelect`, with options from `me.publishers`. It is hidden when there is only one option, which is the case for department staff.
  - `AudienceFields`, with multi-selects for department, programme and intake, and a live summary such as "Computing students, 2024-SEP intake". Leaving all of them empty means all students. That option is offered only to university admins. For department staff, the department is preselected and locked, and the programme list is limited to their department. This is only a convenience, because the API enforces the same rule.
  - `MarkdownField`, a textarea with a preview tab rendered by react-markdown.
  - `FileField`, which uploads to `manage/documents/` and returns an id.
- **Timetable management:** term selector, then courses, then sections, then weekly meetings. Meetings are edited inline. The import screen is added with the first import adapter.
- **Staff home** (`/staff`): shortcuts to create each content type, plus the user's recent drafts.

### API layer

```ts
// shared/api/client.ts
export const api = axios.create({ baseURL: import.meta.env.VITE_API_URL, withCredentials: true,
                                  headers: { "X-Client": "web" } });
// request: Authorization: Bearer <tokenStore.access>
// response: on 401 → single-flight POST /auth/jwt/refresh/ → retry once → else logout()
```

- The access token is kept in memory only.
- When the app starts, it calls `jwt/refresh/`, which sends the httpOnly cookie. If that succeeds, it loads `users/me/`.
- `ApiError {code, message, fields}` reads the backend's error format. Forms pass `fields` to React Hook Form's `setError`.

### React Query usage

- Each feature has query key factories, such as `announcementKeys` and `manageAnnouncementKeys`.
- Defaults: `staleTime: 30s` and `retry: 1`, with no retries for 4xx errors.
- Manage mutations invalidate the manage lists, the read lists and `['dashboard']`.
- The notification count refetches every 60 seconds while the tab is visible.

### Routing

```
/login  /register  /verify-email/:uid/:token  /forgot-password  /reset-password/:uid/:token   (AuthLayout)
/                          student dashboard              (AppLayout, RequireAuth)
/onboarding                profile completion (students with !profile_complete are redirected here)
/announcements[/:id]  /events[/:id] (?view=list|calendar)  /timetable (?view=today|week)  /timetable/sections
/communities[/:slug]  /applications[/:id]  /documents[/:id]  /notifications  /search?q=  /profile
/staff                     staff home                     (StaffLayout, RequireAuth + any *.manage capability)
/staff/announcements[/new|/:id]   /staff/events[...]   /staff/documents[...]   /staff/applications[...]
/staff/communities[...]   /staff/timetable[...]   /staff/academics[...]   /staff/users
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
| Refresh token | httpOnly cookie | `expo-secure-store` | Only the transport differs |
| Navigation and UI | React Router, Tailwind | Expo Router, RN components | No |
| Notifications | In-app polling | Expo push through a new `Device` endpoint | The same `Notification` rows |
| Deep links | `/events/42` | `uniflow://events/42` | Both built from `(target_type, target_id)` |

The mobile app will cover the student side. Staff management stays on the web.

The backend already supports mobile:

- No endpoint depends on cookies.
- Media URLs are absolute.
- The API is versioned.
- The dashboard is a single endpoint.
- Notification targets are type and id pairs rather than web URLs.
