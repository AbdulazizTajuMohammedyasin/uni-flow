# Public Home Page Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Visitors who are not logged in see a public home page at `/` that explains UniFlow and how to use it; logged-in users still get "For you" there.

**Architecture:** `RequireAuth` renders a lazy-loaded `HomePage` instead of redirecting to `/login` when a logged-out visitor is exactly at `/`. Every other private route keeps its current redirect. The page is static (no API calls) and shows README screenshots made with synthetic data.

**Tech Stack:** React 19, React Router 8, Tailwind 4 with the existing tokens, shadcn `Button`, lucide-react, Vitest with Testing Library, Playwright (existing `smoke` and `a11y` projects).

**Spec:** [home-page-design.md](home-page-design.md)

## Global Constraints

- No new dependencies. No backend, API, auth or data changes.
- No invented numbers, testimonials, logos or features. No real student data in images.
- No "how it's built" section and no GitHub link. No video.
- Existing tokens, lime and ink brand, Inter, light and dark themes, existing UI components.
- Responsive at 390 px and 1440 px with no sideways scrolling (the smoke test checks 360/390/768/1024/1440).
- WCAG 2.2 AA: one `h1`, one `main`, logical headings, alt text on every screenshot, visible focus, 44 px tap targets on phones.
- No commits unless the user asks (CLAUDE.md). Work stays on `main`.

## Review Focus

1. **Session still restoring at `/`:** show the existing `PageLoading`, never a flash of the home page for a logged-in user. (Task 1 test.)
2. **Logged-out visitor on another private page** (`/sources`): still sent to `/login?next=%2Fsources`. (The existing test stays green.)
3. **Logged-in user at `/`:** "For you", not the home page. (The existing test stays green.)
4. **Phone at 360 px:** no sideways scrolling, even with the wide desktop screenshots. (Task 3 smoke.)
5. **Keyboard user:** the "How it works" and "Features" links reach their sections, and focus stays visible on every link. (Task 3 a11y.)

---

### Task 1: Logged-out visitors at `/` see the home page

**Files:**
- Create: `frontend/src/pages/Home/Home.tsx` (a minimal `HomePage`: `<main>`, the `h1`, and the Sign up and Log in links; Task 2 fills it in)
- Modify: `frontend/src/components/RequireAuth.tsx`
- Test: `frontend/src/router.test.tsx` (inside `describe('login protection')`)

**Interfaces:**
- Produces: `export function HomePage(): JSX.Element` in `@/pages/Home/Home`. Its `h1` text is exactly `All your AIU announcements, sorted for you`. It has links named `Sign up` (to `/register`) and `Log in` (to `/login`).

- [ ] **Step 1: Write the failing tests** in `router.test.tsx`

```tsx
it('shows the public home page to visitors at /', async () => {
  vi.mocked(authApi.restoreSession).mockResolvedValue(false)
  const router = renderAt('/')
  expect(
    await screen.findByRole('heading', { level: 1, name: 'All your AIU announcements, sorted for you' }, { timeout: 5000 }),
  ).toBeTruthy()
  expect(router.state.location.pathname).toBe('/') // not sent to /login
  expect(screen.getAllByRole('link', { name: 'Sign up' })[0].getAttribute('href')).toBe('/register')
  expect(screen.getAllByRole('link', { name: 'Log in' })[0].getAttribute('href')).toBe('/login')
  expect(screen.queryByRole('navigation', { name: 'Sidebar' })).toBeNull()
})

it('shows the loading state, not the home page, while the session is restoring', async () => {
  vi.mocked(authApi.restoreSession).mockReturnValue(new Promise(() => {})) // never answers
  renderAt('/')
  expect(await screen.findByRole('status')).toBeTruthy()
  expect(screen.queryByRole('heading', { name: 'All your AIU announcements, sorted for you' })).toBeNull()
})
```

- [ ] **Step 2: Run the tests and confirm they fail**

Run: `npm test -- src/router.test.tsx`
Expected: the first new test FAILS (the URL becomes `/login`). The second may already pass. The other tests pass.

- [ ] **Step 3: Implement**
  - Create the minimal `HomePage` described above.
  - In `RequireAuth`, after the `isLoading` check: if `!user && location.pathname === '/'`, return `<Suspense fallback={<PageLoading />}><HomePage /></Suspense>`. Load `HomePage` with `React.lazy`, so the student area doesn't download it.
  - Update the doc comment to list the new rule.

- [ ] **Step 4: Run the tests and confirm they pass**

Run: `npm test -- src/router.test.tsx`
Expected: all pass, including the existing ones listed in Review Focus 2 and 3.

---

### Task 2: The home page content

**Files:**
- Modify: `frontend/src/pages/Home/Home.tsx`
- Create: `frontend/src/assets/home/{for-you,timetable-week,search,notifications-dark,phone-for-you}.png`, copied from `docs/screenshots/` (made by `npm run screens:readme` with synthetic data). Add a one-line comment in `Home.tsx` saying where they come from.
- Test: `frontend/src/pages/Home/Home.test.tsx`

**Interfaces:**
- Consumes: `HomePage` from Task 1; `Wordmark` from `@/components/Wordmark`; `Button` (`asChild`, `size="lg"`, `variant="outline"`) from `@/components/ui/button`.

**Sections, in order** (the copy is the builder's, in the app's plain, short tone; the headings are pinned for the tests):

| # | Element | Heading / id |
|---|---|---|
| 1 | `<header>` with `Wordmark` linking to `/`, a `nav` labelled `Home page` containing `How it works` → `#how-it-works` and `Features` → `#features` (hidden below `sm`), plus `Log in` (outline) and `Sign up` | — |
| 2 | Opening section: `h1`, a supporting line, Sign up and Log in buttons, the `for-you.png` screenshot (`phone-for-you.png` below `md`, using `<picture>`) | h1 `All your AIU announcements, sorted for you` |
| 3 | The problem | h2 `Important messages get buried` |
| 4 | Four numbered steps (`<ol>`) | h2 `How to use UniFlow`, `id="how-it-works"` |
| 5 | Feature tour: For you, Search, Timetable and class changes, Notifications and the daily digest, each an h3 with a screenshot | h2 `What UniFlow does for you`, `id="features"` |
| 6 | Trust points with a link to `/privacy` | h2 `Built to be trusted` |
| 7 | Closing call to action with Sign up and Log in, plus "Sign-up needs an AIU student email (@student.aiu.edu.my)." | h2 `Ready to start?` |
| 8 | `<footer>`: wordmark, `Privacy notice`, `Log in` | — |

**The four steps** (text pinned by the spec):
1. Sign up with your `@student.aiu.edu.my` email.
2. Choose your school, programme and intake.
3. Add the groups you're in, and add your timetable.
4. Read what matters on "For you", get alerts, and confirm class changes on your timetable.

**Visual notes:**
- Reuse `AuthLayout`'s language: the lime `bg-primary` band for the opening section, ink text, rounded-2xl `bg-card ring-1 ring-border` frames around screenshots, and a `max-w-6xl` content width.
- Images get `loading="lazy"` (except the first), explicit `width` and `height`, and `h-auto w-full`.
- Section ids get `scroll-mt-*`, and `scroll-smooth` only under `motion-safe`.

- [ ] **Step 1: Write the failing tests** in `Home.test.tsx` (render `HomePage` inside `createMemoryRouter([{ path: '/', element: <HomePage /> }])`)
  - `it('explains how to use UniFlow in four steps')`: the heading `How to use UniFlow` exists; `within(list).getAllByRole('listitem')` has length 4; the first item contains `@student.aiu.edu.my`.
  - `it('links the top navigation to sections on the page')`: within the `navigation` named `Home page`, the `How it works` link href is `#how-it-works` and the `Features` link href is `#features`; elements with those ids exist.
  - `it('gives every screenshot a description')`: every `img` has a non-empty `alt`.
  - `it('links to the privacy notice')`: at least one link named `Privacy notice` has href `/privacy`.
  - `it('has exactly one h1')`: `getAllByRole('heading', { level: 1 })` has length 1.

- [ ] **Step 2: Run the tests and confirm they fail**

Run: `npm test -- src/pages/Home`
Expected: FAIL (the sections don't exist yet).

- [ ] **Step 3: Implement the sections and copy the screenshots**

- [ ] **Step 4: Run the tests, typecheck and lint**

Run: `npm test` then `npm run typecheck` then `npm run lint`
Expected: all pass, with no lint errors.

---

### Task 3: Browser checks, screenshots and docs

**Files:**
- Modify: `frontend/e2e/routes.ts`: add `{ name: 'home', path: '/', scenario: 'visitor', ready: 'All your AIU announcements, sorted for you' }` as the first entry under "Not logged in".
- Modify: `docs/05-frontend.md` (a "Home (`/`, public)" bullet in the student area list, and the routing note that logged-out `/` shows it), `docs/ui-ux/page-inventory.md` (the new public route), `docs/ui-ux/iteration-log.md` (an entry for the iterations), `docs/PROGRESS.md` (one plain line).

- [ ] **Step 1: Run the browser checks**

Run: `npm run e2e` (the `smoke` project runs both `smoke.spec.ts` and `a11y.spec.ts`)
Expected: the `home` checks pass: no console errors, 44 px taps, no sideways scrolling at any width, one h1, keyboard focus visible. The existing pages are unchanged, including `for-you--loading`. Any failure gets investigated, not skipped.

- [ ] **Step 2: Capture and inspect screenshots**

Run: `npm run screens`, then look at `home` in light and dark at phone and desktop sizes (`artifacts/ui/…`).
Expected: write a P0–P3 issue list, fix P0 and P1 first, and do at most 3 iterations. Log each one in `iteration-log.md`.

- [ ] **Step 3: Update the docs** listed above, in a professional tone.

- [ ] **Step 4: Final check**

Run: `npm test && npm run typecheck && npm run lint`, then `git status` and `git diff --stat`.
Expected: everything passes, and the only files changed are the ones listed in this plan.
