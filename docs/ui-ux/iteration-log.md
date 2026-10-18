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

## UI-5: Groups, Search, Notifications (2026-10-18)

**Changes**
- `components/ui/tabs.tsx` (new, `npx shadcn@latest add tabs`; it uses `radix-ui`, which was already installed).
- `lib/notifications.ts`: `NEEDS_YOU_KINDS` (named, action required, class change to confirm), `dayLabel()` ("Today", "Yesterday", "Fri 16 Oct" in Malaysia time) and `groupByDay()`.
- `pages/Notifications/Notifications.tsx`:
  - "All" / "Needs you (n)" tabs, filtered on the client; "All" is the default, so nothing is hidden on arrival.
  - Alerts grouped under day headings (each a labelled region).
  - Each row has an icon for its kind; unread rows show a dot, the word "New" and a bold title (not colour alone).
  - A list skeleton while loading; an empty state for an empty "Needs you" tab.
- `pages/Search/Search.tsx`: a larger field with a search icon (`type="search"`), and a result count ("1 result for “petronas”") announced as a status.
- `pages/Sources/Sources.tsx` (Groups):
  - The groups are one divided list; each has a platform icon and a status badge with icon and word: Connected, Waiting to join, Disconnected (no badge for pasted or staff groups).
  - Waiting and disconnected groups get one line saying what that means ("New messages from this group are ignored." is the admin action's own wording).
  - "Paste messages" / "Upload WhatsApp export" moved into one "Add messages" menu per group; the chosen form opens in a titled box with a Close button, and focus moves into it.
  - A disabled "Add group" says why ("Type a group name first.", linked with `aria-describedby`).
- Tests: 5 new unit tests (day names and groups, "New", the "Needs you" tab, the disconnected badge, the Add group hint), plus a result-count check in the existing Search test; Groups tests open the menu from the keyboard.
- e2e: two new screens, `notifications-needs-you--busy` and `groups-paste--busy` (with actions in `screens.spec.ts`).

**Iteration 01** (`artifacts/ui/ui5-iteration-01/`, light and dark, phone/laptop/desktop)
- P1: after choosing "Paste messages" from the menu, focus went nowhere (the menu's focus trap stopped `autoFocus`). Fixed: the menu's close handler moves focus to the chosen form's field.
- P2: the paste box said "Paste messages" twice (title and field label). The field label is now screen-reader-only.
- P3: uneven space after "New ·".

**Iteration 02** (`artifacts/ui/ui5-iteration-02/`)
- P1 (smoke test): the tabs were 37 px tall on phones. They are now 44 px on phones and 32 px from `md`.
- No P0–P2 issues left in the captured screens.

**Checks:** `npm test` (all unit tests), `typecheck`, `lint` and `npm run e2e` (smoke).

## UI-4: Timetable (2026-10-17)

**Decision change:** the user shared AIU's official timetable image (BCS2B, Semester 2 25/26): days as rows, one-hour slots 8:30–22:30 as columns. The desktop week view follows that format instead of the planned 7 day-columns.

**Changes**
- `components/WeekGrid.tsx` (new): a semantic `<table>` (caption, day row headers, a time column header).
  - The hour columns are on AIU's :30 grid, 08:30–22:30, widened to fit classes outside that range.
  - Class blocks are positioned by minutes. Overlapping classes are split into lanes.
  - Today's row is accent-tinted and labelled "Today", with a now-line behind the blocks and a "Now" tag in the class.
  - Pending changes get an attention ring and label; confirmed changes get a label; cancelled classes are struck through.
  - The table scrolls inside its card (`min-w-[60rem]`), never the page.
- `hooks/useMediaQuery.ts` (new): the grid renders only at ≥1280 px. Jsdom has no media queries, so tests see the list.
- `pages/Timetable/Timetable.tsx`:
  - Order: header, shared-timetable offer, classes (Today or Week), changes to confirm (`#changes`), My sections.
  - The week view has an attention notice linking to `#changes`, and a date range between the chevron buttons (labels hidden on phones, accessible names "Previous week" / "Next week").
  - Day lists are divided row lists, with Now / Next on today.
  - My sections: name on its own line; a quieter Remove; "Add classes" with icons and `aria-expanded`; the open tool sits in a titled box with a Close button.
  - The page widens to the full content width in the week grid.
- `components/ClassChanges.tsx`: an explanation line, the change text in bold, one divided list, and wrapping buttons. Accessible names are unchanged.
- `lib/timetable.ts`: `todayIsoInMalaysia()`.
- Tests:
  - `Timetable.test.tsx`: the button name "Next week →" becomes "Next week" (the arrow is now an icon). This is the only test edit.
  - `WeekGrid.test.tsx` (new): row layout, the hour range widened for a 23:30 class, the change label, and the Now tag.
- E2E: the week screen's ready text is now "19 Oct – 25 Oct".

**Iteration 01** (`artifacts/ui/ui4-iteration-01/`)
- P2: the now-line was drawn over the class text.
- P2: rooms were truncated ("B09_…").
- P2: on phones, the course name wrapped beside the code in My sections.

**Iteration 02** (`artifacts/ui/ui4-iteration-02/`)
- Fixes: the now-line moved behind the blocks; the room got its own line, with taller rows (6.5rem); the course name moved to its own line.
- P3 left: the "Now" tag was truncated ("No…") next to the course code.

**Iteration 03** (`artifacts/ui/ui4-iteration-03/`)
- Fix: "Now" moved to the time line. Checked by eye: `timetable-week--busy` (light, desktop).

**Iteration 04** (2026-10-18, `artifacts/ui/ui4-iteration-04/`, after user feedback)
- The user still saw rows, not a table. Cause: the grid only showed from 1280 px. A typical laptop (1366×768 at Windows' 125% scaling) gives the browser ~1093 px, so it got the list.
- Fixes:
  - The grid now shows from **1024 px**.
  - The table min width went from 60rem to 46rem (day column `w-20`, tighter block padding), so it fits at ~1093 px with no inner scrolling.
  - A new `laptop` (1093×614) screenshot viewport in `e2e/routes.ts`.
- At that width:
  - "Now" moved to its own label line, and the current class is filled primary.
  - The time no longer wraps; change labels truncate with the full text in the block's tooltip.
- Checked by eye: `timetable-week--busy` (laptop, light and dark).

**Follow-up** (2026-10-18, real data)
- The user still saw no table. Checking their real data: all 7 sections are in "2025/2026 Semester 3" (3 Aug – 2 Oct 2026), the term has ended, and no 2026/27 term exists yet. So `timetable/week/` correctly returns no classes, and the grid drew seven empty rows.
- This is data, not a layout bug.
- UI fix: a whole empty week now shows "No classes this week" with the term name and what to do (use the arrows, or add new classes), instead of an empty table.
- Test: `Timetable.test.tsx` covers the empty-week message.

**Checks:**
- `npm test`: 122 passed. `typecheck` and `lint`: clean.
- `npm run e2e`: 196 passed. 2 checks (register at 768 px, the account menu) timed out once while the user's own dev servers were also running; they passed on re-run, so this is load, not app behaviour.

## UI-3: For you, item page, digest (2026-10-17)

**Changes**
- `pages/ForYou/ForYou.tsx`:
  - "Needs you (n)" (h2) groups the Direct attention and Action required levels (h3, amber list edge, icons). Important updates and Digest are h2.
  - Digest rows are compact, with a link to `/digest`.
  - The page description includes today's date (Malaysia time).
  - From `xl` (1280 px) up: two columns, with the Today rail on the right, sticky.
  - The four level regions and their names are unchanged (the tests depend on them), and the API calls are unchanged.
- `components/TodayBox.tsx`: the Today rail, a timeline with "Now", "Next" and greyed-out finished classes (in words, not colour alone). The pending-change note is in the attention style. Uses the new `nowInMalaysia()` and `todayInMalaysia()` in `lib/timetable.ts`.
- `components/ItemRow.tsx` (new, replaces `FeedItemCard.tsx`): `ItemList` (one bordered list with dividers, optional attention edge) and `ItemRow` (unread dot with the "Unread" label, title, Official / Not confirmed badges, 2-line summary, byline). Also used by Search.
- `components/ListSkeleton.tsx` (new) plus shadcn `ui/skeleton.tsx`: loading rows with `role="status"`, `aria-busy` and an sr-only "Loading…". The pulse animation stops under reduced motion. Used by For you, Insight, Digest and Search.
- `components/BackLink.tsx` (new): goes back in history when there is one, otherwise links to For you. Used by Insight and Digest.
- `pages/Insight/Insight.tsx`:
  - "Why you see this" sits under the title with a primary rule.
  - When / Deadline / Where are an icon grid.
  - "What to do" and the pending-change note are attention panels.
  - "Open the link" and "Open original" are outline buttons (same accessible names).
  - Evidence is one divided list; the actions sit under a divider.
  - The mark-as-read and dismiss / not-relevant behaviour is untouched.
- `pages/Digest/Digest.tsx`: groups with counts, divided list rows, `BackLink`, skeleton.
- Tests:
  - For you: "Needs you (2)" plus the digest link, and the Today rail's Now / Next with the time frozen.
  - Insight: Back returns to the previous page, and the "For you" link shows when the page is opened directly.

**Iteration 01** (`artifacts/ui/ui3-iteration-01/`)
- Checked by eye: `for-you--busy` (light desktop, dark phone), `insight--busy` (light desktop), `for-you--loading` (light phone), `digest--busy` (dark desktop).
- **P2:** the digest still had the old plain "← For you" text link, inconsistent with the item page.

**Iteration 02** (`artifacts/ui/ui3-iteration-02/`)
- Fix: the shared `BackLink`. Checked by eye: `digest--busy` (light phone).

**Checks:**
- `npm test`: 119 passed (4 new). `typecheck` and `lint`: clean.
- `npm run e2e`: 196 passed.

**Still a proposal (needs an API change, not done):** showing the source group on feed rows (redesign plan, section 9).

## UI-2: app frame (2026-10-17)

**Changes**
- `lib/navigation.ts`: a `lucide-react` icon per student nav item.
- `components/AppLayout.tsx`:
  - The sidebar has icons, an active state (tinted background + 4 px primary bar + semibold + `aria-current`), focus rings, a sticky full-height layout, and the account card at the bottom.
  - The phone top bar has the wordmark plus the account menu.
  - The bottom bar has icon + label (56 px tall), the unread badge on the bell, and safe-area padding.
  - Content is centred in `max-w-5xl` with larger desktop gutters.
- `components/AccountMenu.tsx` (new): shadcn `dropdown-menu` with name, email, Profile, Privacy notice, Staff dashboard (staff only) and Log out. It is 44 px per item on phones and keyboard-accessible (Radix). It is a full card in the sidebar and initials in the phone bar.
- `components/ui/dropdown-menu.tsx`: added with `npx shadcn add dropdown-menu`.
- `components/PageHeader.tsx` (new): one title style (22 px on phones, 28 px from `md` up, semibold, balanced wrapping), an optional description (max 65 characters per line) and actions. Used on For you, Timetable, Groups, Search, Notifications, Digest, Profile and the staff placeholders. The Insight page keeps its own header until UI-3.
- E2E: a new `account-menu--busy` screen (menu opened before the screenshot).

**Iteration 01** (`artifacts/ui/ui2-iteration-01/`)
- **P2:** on desktop the account menu was wider than its trigger, aligned to the end, so it was pushed against the window's left edge.
- Checked by eye: `for-you--busy` (light, desktop), `notifications--busy` (light, phone), `timetable-today--busy` (dark, desktop), `account-menu--busy` (dark phone, light desktop).
- Note: full-page screenshots cut the sticky sidebar off after the first screen. This only affects the screenshots; in the browser the sidebar stays visible while scrolling.

**Iteration 02** (`artifacts/ui/ui2-iteration-02/`)
- Fix: the sidebar menu takes the trigger's width. Checked by eye: `account-menu--busy` (dark, desktop).

**Checks:**
- `npm test`: 115 passed (3 new for `AccountMenu`).
- `typecheck` and `lint`: clean.
- `npm run e2e`: 196 passed.

**Left for later:** in the For you Today box on phones, a "Room changed" badge wraps onto its own line (UI-3, Today rail).

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
