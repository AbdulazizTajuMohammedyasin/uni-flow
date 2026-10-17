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
