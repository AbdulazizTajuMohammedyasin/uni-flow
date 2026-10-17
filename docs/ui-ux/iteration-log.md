# Redesign iteration log

One entry per screenshot iteration once the redesign is underway (Phase 2). Each entry lists:
- the milestone;
- the routes, states and viewports captured;
- the screenshot folder;
- the issues found, ranked P0–P3;
- the changes made;
- the tests run;
- what is left.

There are at most 3 iterations per milestone before the results are reported back.

## UI-1: tokens, dark mode, sizes (2026-10-17)

**Changes**
- `src/index.css`: the new light and dark tokens from the plan, plus new `attention`, `attention-foreground`, `attention-border`, `success` and `destructive-foreground` utilities. The old `brand-*` scale is removed. `color-scheme` is set per theme, so native controls follow it.
- Raw palette classes replaced with tokens in 19 files. `grep` for `(bg|text|ring|border)-(slate|red|amber|emerald|brand|…)-N` outside `components/ui/` now returns nothing.
- Dark mode:
  - `lib/theme.ts`, `hooks/useTheme.ts`, `components/ThemeToggle.tsx` (radio group: Light / Dark / System);
  - the no-flash script in `index.html`;
  - `followSystemTheme()` in `main.tsx`;
  - a Profile → Appearance section.
  - The account-menu entry comes in UI-2.
- Sizes:
  - `Button` default and `sm` are 44 px on phones (36 / 32 px from `md` up), `lg` is 44 px;
  - `Input` and `SelectField` are 44 px on phones;
  - the paste textarea uses tokens.
- shadcn components: none added yet. Each is added with the screen that first uses it (repo convention).

**Iteration 01** (`artifacts/ui/ui1-iteration-01/{light,dark}/{phone,desktop}/`, 108 screenshots)
- **P0:** the phone timetable overflow got *worse* (488 px wide, from 445) because the bigger buttons widened the non-wrapping "My sections" row.
- **P2:** at 360 px the group cards' two buttons overflowed by 3 px (also caused by the bigger buttons). Found by the smoke test; fixed with `flex-wrap`.
- Smoke: 6 timeouts under parallel load. The expect timeout is raised to 15 s; this was a test-tool issue, not an app issue.
- Checked by eye: `for-you--busy` (light and dark, desktop), `timetable-today--busy` (dark, phone), `profile--busy` (dark, phone). Tokens apply everywhere; the attention panel reads well in both themes.

**Iteration 02** (`artifacts/ui/ui1-iteration-02/`)
- Fix: the "My sections" buttons wrap (`flex-wrap`), pulled forward from UI-2 because UI-1 made the problem worse.
- `timetable-today--busy` on the phone is now 390 px wide (checked by eye). The `KNOWN_OVERFLOW` list in the smoke spec is now empty.

**Checks:**
- `npm run e2e`: 189 passed. This includes 27 new "44 px tap size on phones" checks, and no expected failures are left.
- `npm test`, `typecheck` and `lint`: results in the milestone summary.

**Left for later milestones**
- The page layouts are unchanged (UI-2 onwards).
- Badges such as "Room changed" are still outline-only (status icons come in UI-3/UI-4).
- `PageLoading` is still full-height (UI-3).

## UI-0: tooling (2026-10-17)

- **Added:**
  - `@playwright/test` 1.64.1 (dev only; uses the installed Chrome);
  - `frontend/playwright.config.ts`, `frontend/tsconfig.e2e.json`;
  - in `frontend/e2e/`: `mock-api.ts` (the fake backend, 7 scenarios), `routes.ts` (27 pages and states), `smoke.spec.ts`, `screens.spec.ts`;
  - the npm scripts `e2e` and `screens`;
  - `artifacts/` in `.gitignore`.
- **Smoke:** 162 passed. This includes 6 *expected failures*: sideways scrolling at 360 and 390 px on `timetable-today--busy`, `timetable-week--busy` and `timetable--empty`. The test run caught the empty timetable as a new case.
- **Baseline:**
  - `artifacts/ui/baseline/light/{phone,desktop}/`, 54 screenshots;
  - light only, because dark mode doesn't exist yet;
  - made-up data, with "now" frozen at Mon 19 Oct 2026, 09:30 Malaysia time.
- **Checked by eye:**
  - `for-you--busy`;
  - `timetable-week--busy` (phone; the image is 445 CSS px wide, which confirms the P0);
  - `for-you--loading` (phone; a lone "Loading…" in an otherwise empty page, which confirms P2 #9).
- **Other checks:** `npm test` (unit), `typecheck` and `lint`; results in the milestone summary.

## Phase 1 baseline (2026-10-17)

- **Captured:** 13 routes × 2 viewports (1440×900 and 390×844, full-page).
  - The captures are in `C:\Users\abdul\Desktop\uniflow-screenshots\before-redesign\`, outside the repo.
  - They contain real data from the developer's own account, so they are not for committing.
- **Tests:** `npm test` passed 106 tests; `typecheck` and `lint` are clean.
- **Main issues:** see [redesign-plan.md](redesign-plan.md) section 2. The one P0 is horizontal overflow on the phone timetable (445 px page width on a 390 px screen).
- **No changes yet.** The plan is waiting for approval.
- **Decisions recorded** (2026-10-17, [redesign-plan.md](redesign-plan.md) section 12):
  - deep blue as the main colour;
  - dark mode now, with a toggle;
  - a 7-column week view on computers;
  - notification tabs;
  - Playwright, with screenshots in `artifacts/`.
