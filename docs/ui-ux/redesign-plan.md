# UniFlow UI/UX redesign plan (Phase 1: proposal, not approved yet)

Inputs:
- [page-inventory.md](page-inventory.md): routes, issues, evidence.
- [reference-research.md](reference-research.md): references and skill findings.

Nothing in this plan changes the backend, the API, routes, auth, the data model or any business rule. Items that *would* need such a change are listed separately as **proposals**.

## 1. Current strengths (keep these)

- **The right information architecture already exists.**
  - Four priority tiers (direct, action, important, digest).
  - A "why you see this" reason on every item.
  - Source quotes with "Open original".
  - Class changes need the student's confirmation.
- **Good accessibility foundations.**
  - Real labels via `FormField`.
  - `role="alert"` / `role="status"` on messages.
  - `aria-pressed` on view toggles.
  - Descriptive `aria-label`s on Confirm, Reject and Remove.
  - A mobile bottom nav with 44 px targets.
- **Plain, specific copy**, for example "Untick any class you don't take." and "Confirm or reject".
- **Clean structure:** one page folder per route, shared form components, and 106 passing tests that query by role and text.

## 2. Problems ranked by impact

| # | P | Problem | Evidence |
|---|---|---|---|
| 1 | **P0** | The phone timetable scrolls sideways: the page is 445 px wide on a 390 px screen. | `Timetable.tsx` "My sections" header `flex gap-2`; `phone/11` |
| 2 | P1 | Every priority looks the same. "You were named" and "good to know" use an identical white card; the tier shows only as a small heading. | `ForYou.tsx`, `FeedItemCard.tsx`; `desktop/10` |
| 3 | P1 | Trust information is visually demoted: "Why you see this", the source group and the original quotes are grey and secondary, and feed cards don't show the source at all. | `Insight.tsx`, `FeedItemCard.tsx` |
| 4 | P1 | Desktop wastes about half the screen: content is capped at `max-w-3xl` next to a 240 px sidebar on a 1440 px screen. | `AppLayout.tsx`, every desktop screenshot |
| 5 | P1 | On the timetable, the "classes may have changed" box comes before today's classes and takes the whole first screen. The three "add" buttons look the same as selected toggles, and panels open below the list. | `desktop/11` |
| 6 | P1 | The phone profile is one 2,500 px column with no section navigation. | `phone/17` |
| 7 | P1 | Input borders are hard to see. The current `--input` (about `#e5e5e5`) has roughly **1.3:1** contrast on white, below the WCAG 1.4.11 minimum of 3:1 for component boundaries. | `index.css` `--input`; computed |
| 8 | P2 | Buttons are 28–36 px tall, below the project's own 44 px phone target. | `ui/button.tsx`; [05-frontend.md](../05-frontend.md) line 134 |
| 9 | P2 | Loading is a full-height "Loading…" text, used inline in 11 places, and the layout jumps. | `PageLoading.tsx` |
| 10 | P2 | Raw colour classes in 19 files bypass the tokens; there are no semantic attention, success or danger tokens. | grep counts in the inventory |
| 11 | P2 | The nav has no icons (`lucide-react` is installed but unused); phone users have no logout or menu except via Profile. | `AppLayout.tsx` |
| 12 | P2 | The digest page can't be reached from the navigation; the Insight back link always says "For you". | `navigation.ts`, `Insight.tsx` |
| 13 | P2 | The auth pages give no hint of what UniFlow is; the privacy notice sits in a narrow card. | `AuthLayout.tsx`; `desktop/01`, `desktop/04` |
| 14 | P3 | Visual identity is the default shadcn kit (indigo, rounded cards, soft shadows everywhere). | `index.css`; the frontend-design skill's "SaaS-card kit" tell |

## 3. Recommended visual direction: "The quiet notice board"

**Subject.** UniFlow takes a noisy pile of WhatsApp group messages and turns it into a short, trustworthy list of what affects *you*, plus your classes.

The design should feel like a well-kept university notice board:
- calm,
- ordered by urgency,
- every notice signed with where it came from.

It should not look like a SaaS analytics dashboard: no KPI cards and no charts. There is no real student use for them.

**Principles**
1. **Urgency is the only loud thing.** One attention colour, used only for "needs you": named, action required, a change to confirm. Everything else stays in ink and greys.
2. **Every item is signed.** Source group and time sit on the same line as the item, styled like a byline, in normal text colour (not faded). This needs one API field, so it is a proposal; see section 9. Until then, show the `reason`, which already exists, in that byline.
3. **Lines, not boxes.** Replace stacks of shadowed cards with grouped lists separated by hairlines. A raised surface is reserved for things you act on: the change to confirm, and forms.
4. **The one memorable element is the "Today" rail.** A compact time strip of today's classes with a "now" marker, and change states shown inline with a word and an icon ("Moved", "Cancelled"). It appears on For you and on Timetable (references: Sunsama's now-line, Cal.com rows). This is where the design spends its boldness.
5. **Plain language stays.** Keep the current copy style. Buttons name their result ("Confirm change", "Remove section").

### Tokens (proposed)

These are additions to and replacements for the values in `index.css`, still exposed as shadcn semantic variables. They are named here in plain English.

| Token | Value | Use | Contrast (computed) |
|---|---|---|---|
| ink (`--foreground`) | `#17212F` | Text | 15.0:1 on paper |
| paper (`--background`) | `#F5F6F8` | Page | — |
| surface (`--card`) | `#FFFFFF` | Lists and panels | — |
| muted text (`--muted-foreground`) | `#586273` | Secondary text | 5.7:1 on paper, 6.2:1 on white (the current value is 4.5:1) |
| line (`--border`) | `#D5DAE1` | Dividers (decorative) | — |
| control edge (`--input`) | `#8C95A3` | Input and checkbox borders | 3.0:1 (fixes problem #7) |
| primary | `#1B5E9E` (deep "harbour" blue) | Links, primary buttons, focus ring | 6.7:1 both ways with white |
| attention (new) | text `#8A4B00` on `#FFF4DB` | "Needs you", changes to confirm | 6.2:1 |
| success (new) | `#17663A` | "Saved", "Added" | 7.0:1 |
| danger (`--destructive`) | `#B42318` | Errors, the unread count | 6.6:1 |

- **Why blue, not the current indigo:** it is decision #2 below.
  - The deep blue reads as institutional and trustworthy, and it is not the default shadcn indigo.
  - If AIU has official brand colours, they replace `primary`, and the rest stays.
- **Type:** keep **Geist Variable**, which is already installed, so no new dependency.
  - Scale: 13 / 14 / 16 (body) / 18 / 22 / 28 px.
  - Page titles at 22 px on phones (smaller than today's 24 px), to bring content above the fold.
  - `tabular-nums` for all times.
  - One family, no ALL-CAPS labels.
- **Radius:**
  - 8 px for controls and list containers.
  - 12 px for the attention panel only.
  - No pills, except chips.
- **Elevation:**
  - No shadow on lists.
  - One subtle shadow for sticky bars and popovers.
- **Spacing:** a 4 px base, with 16 / 24 px page gutters (phone / desktop).
- **Motion:**
  - About 150 ms colour and opacity transitions on state changes only.
  - No entrance animations.
  - `prefers-reduced-motion` respected.
- **Dark mode:** not in this redesign (decision #6). The tokens stay dark-ready.

### Layout

- **Desktop (≥1024 px):**
  - A sidebar with icons (Linear-like).
  - Main column up to 720 px.
  - On ≥1280 px, a right rail with the Today rail and the pending-changes summary on For you; the timetable gets a wider week grid.
- **Tablet (768–1023 px):** the sidebar collapses to icons with labels underneath, or stays at 200 px. Single column.
- **Phone (<768 px):**
  - Top bar with the wordmark and an account menu (Profile, Privacy, Log out).
  - Bottom nav with icon + label, 5 items, unchanged.
  - Every row at least 44 px tall.

## 4. Page-by-page changes (presentation only)

| Page | Changes |
|---|---|
| **App shell** | Icons on nav items; an active state with a primary bar and text weight, not colour alone; an account menu on phones (shadcn `dropdown-menu`); the unread count as a danger-token badge with its text label kept; the dev `API` badge stays dev-only and moves out of the top bar into the account menu. |
| **For you** | Header: greeting, date and the Today rail. Then **"Needs you"** (the direct + action tiers, plus the class-change prompt), in the attention style with the tier named in text and an icon. Then **"Updates for you"** (important). Then **"Good to know"** (digest tier), collapsed to a count with a link to `/digest`. The tier order and data are unchanged; only the grouping labels change, and the original tier names stay visible as row labels. Item rows: title; summary limited to 2 lines; byline with reason · when; unread dot plus "Unread" text for screen readers. Skeleton rows while loading. |
| **Insight** | Byline and "Why you see this" promoted under the title; a "What to do" block in attention style; quotes as a list with sender, group, time and **Open original** as a real button; Dismiss and "Not relevant to me" grouped at the bottom; the back link uses browser history when there is one, and falls back to "For you". |
| **Timetable** | The Today rail at the top; the "N changes to confirm" panel **below** today's classes (still above the fold on desktop); on desktop the week view becomes 7 columns in CSS grid with no library (decision #4), and stays a day list on phones; "My sections" rows get aligned actions; one **"Add classes"** button opens a choice of the three existing flows (import, choose, add missing), rendered in place with a heading and a close button; the overflow is fixed by wrapping. |
| **Groups** | Status as a badge with an icon and text ("Waiting to join", "Connected", "Disconnected"); the add form explains *why* the button is disabled; paste and upload move into a per-group "Add messages" menu. |
| **Search** | A larger search field; result count; the same item rows as For you. |
| **Notifications** | Grouped by day (Today, Yesterday, then earlier dates); unread shown with dot + bold + the word "New" in the kind line; optional "Needs you / All" tabs filtered **on the client** by notification kind (decision #5). |
| **Digest** | A link from For you's "Good to know"; day header; an empty state that explains when the digest arrives. |
| **Profile** | Section nav (Account, Studies, Interests, Password, Privacy): a sticky left list on desktop, an anchor chip row on phones; one explanation line per setting; save buttons stay per section, as today. |
| **Onboarding** | A "Step 1 of 2" indicator; the same forms. |
| **Auth** | A two-panel layout on desktop: the form, plus a short plain statement of what UniFlow does and the privacy link. A single column on phones. A focused "Check your email" state. The privacy notice gets a readable 65-character text column and section headings. |
| **404 / 403 / error** | Token colours, an icon, the same copy. |
| **Staff placeholders** | Token colours only (decision #3). |

## 5. Components and tokens work

- **`index.css`:** new token values; add `--attention`, `--attention-foreground`, `--success` and `--danger`-foreground utilities.
- **Replace the raw palette classes in all 19 files** with semantic classes.
- **shadcn components to add** (allowed by [05-frontend.md](../05-frontend.md) line 23: "added one at a time … only when a screen needs them"):
  - `skeleton`
  - `tabs` (Today / Week, notification filters)
  - `dropdown-menu` (account menu, group actions)
  - `separator`
- **Not adding:** `sonner` toasts (a new package; inline status messages stay) and the `sidebar` block.
- **Button:** a phone-friendly size (`min-h-11` below `md`) for primary actions; keep `sm` for dense desktop rows only.
- **New small UniFlow components:**
  - `PageHeader`
  - `ItemRow` (replaces `FeedItemCard` visually; same props)
  - `StatusBadge` (icon + text)
  - `TodayRail`
  - `SectionNav`
  - `InlineLoading` (skeleton variant; `PageLoading` stays for route loads)
- **Icons:** `lucide-react`, already a dependency.

## 6. Responsive and accessibility plan

- **Viewports checked every milestone:** 360, 390, 768, 1024, 1440 (and 1280 for the right rail).
- **Automatic overflow check:** `document.documentElement.scrollWidth <= innerWidth` at each viewport, for each route.
- **Targets:** at least 44 px on phones for buttons, nav and rows; at least 24 px everywhere (WCAG 2.5.8).
- **Contrast:** use the token table above; text 4.5:1, control boundaries 3:1. Re-verify with computed values and the browser's contrast checker on the final screenshots.
- **Status never by colour alone:** unread uses a dot + text; tiers use a label + icon; change states use a word; errors use an icon + text.
- **Keyboard:**
  - Visible focus ring in `primary` on every link, button and chip.
  - Tab order matches the visual order.
  - The dropdown menu closes on Escape and returns focus (Radix does this).
- **Screen readers:** keep the existing `aria-label`s and roles. The test suite depends on them.
- **Reduced motion:** all transitions wrapped with `motion-safe:`.

## 7. Functional regression risks and safeguards

| Risk | Safeguard |
|---|---|
| Tests query by text and role (e.g. "Confirm or reject", "Mark all as read", `aria-label="Confirm change to …"`) | Keep accessible names; when copy must change, change it in the same commit as its test and list it in the milestone summary. Run `npm test`, `typecheck` and `lint` after every milestone. |
| Insight marks items read on open; notification click marks read | Don't touch the hooks; only restyle the markup around them. |
| Timetable: changes affect *only my* timetable; imports poll; `?view=week&date=` | Keep the components' logic and URL params; restyle the JSX only. Smoke-test Confirm, Reject, week navigation and import Start → Review. |
| Auth: `safeNext`, refresh cookie, onboarding redirect | No changes in `AuthContext`, `RequireAuth` or `api/`. Login, register and onboarding only restyled. |
| Unread polling every 60 s | `useUnreadCount` unchanged. |
| Grouping tiers into "Needs you" could hide a tier | Every item still shows its tier label; a test asserts all four tiers render. |

## 8. Implementation order (each step is reviewable)

1. **UI-0 Tooling (needs approval, see section 10):** Playwright smoke and screenshot harness with **mocked API responses built from synthetic fixtures**, so no real student data and no backend is needed. Capture the "before" set.
2. **UI-1 Tokens and primitives:** `index.css` tokens; semantic replacements in the 19 files; button sizes; add skeleton, tabs, separator and dropdown-menu. *No layout changes yet.*
3. **UI-2 App shell:** sidebar with icons, phone account menu, bottom nav icons, content widths, the phone overflow fix (problem #1, which may be done first as a hotfix if you prefer).
4. **UI-3 For you, Insight, Digest:** ItemRow, Today rail, "Needs you" grouping, byline.
5. **UI-4 Timetable:** changes panel position, Add classes chooser, desktop week grid (if approved).
6. **UI-5 Groups, Search, Notifications.**
7. **UI-6 Profile, Onboarding, Auth, Privacy, 404/403/error.**
8. **UI-7 Accessibility and regression pass:** final screenshots; keyboard walk-through of every route.

Each milestone:
- at most 3 screenshot iterations;
- a summary of the files changed, tests run and screenshot paths;
- you commit (the project rule).

## 9. Proposals that need backend or API changes (not part of the redesign)

- **Source group on feed list items.** Add `group_title` to `FeedItem` from the first evidence. This needs a serializer change in `backend/apps/intelligence`, a test, and docs.
- **"Next class" hint on a day with no classes.** The week endpoint already returns this data, so the hint can be computed on the client from `timetable/week/`. *No API change*, but it costs one extra request on the For you page. Your decision.

## 10. Screenshot and test workflow (no MCP)

- **Today:** there is no browser tooling in the repo.
- **Smallest proposal** (needs your approval: a new dev dependency and new files):
  - Add `@playwright/test` as a **devDependency** in `frontend/`.
  - Use the **installed Chrome** (`channel: 'chrome'`), so no browser download is needed.
  - Add `frontend/e2e/`, with:
    - `smoke.spec.ts`: each route renders; no console errors; no horizontal overflow at 390 and 1440.
    - `screens.spec.ts`: full-page screenshots per route, state and viewport.
  - Add a `playwright.config.ts`.
  - API calls are intercepted with `page.route('**/api/v1/**')` and answered from synthetic fixtures, extending `src/test/fixtures.ts`. That covers populated, empty, error and loading states, with no real names and no backend.
  - New npm scripts: `e2e` and `screens`.
- **Where screenshots go:**
  - **Option A (recommended):** `artifacts/ui/{baseline,iteration-NN}/`, plus one `.gitignore` line, `artifacts/`.
  - **Option B:** keep them outside the repo, like the baseline in `C:\Users\abdul\Desktop\uniflow-screenshots\`, with no `.gitignore` change.
- **Optional, a second dependency:** `@axe-core/playwright` for automatic accessibility checks. Otherwise the checks are manual: the keyboard walk-through and contrast table above.
- **CI:** not added now. A later option is to run the smoke spec in GitHub Actions.

## 11. Acceptance criteria (measurable)

- No horizontal overflow at 360, 390, 768, 1024 or 1440 on any route, checked automatically.
- On phones, all buttons, nav items and list rows are at least 44 px tall, measured in the smoke spec.
- Text contrast is at least 4.5:1 and control boundaries at least 3:1, per the token table.
- No raw palette classes are left (`grep -E "(bg|text|ring|border)-(slate|red|amber|emerald|brand)-[0-9]"` returns nothing outside `components/ui/`).
- `npm test` passes (106 tests or more), and `npm run typecheck` and `npm run lint` are clean.
- No changes under `backend/`, `frontend/src/api/`, `context/` or `hooks/`, and no route changes in `router.tsx`, except approved proposals.
- The For you first screen at 390×844 with the synthetic "busy day" fixture shows the Today rail and at least the first "Needs you" item.

## 12. Decisions needed from you

1. Inspiration sites: send them, or confirm there are none.
2. Brand: use AIU colours or a logo (send them), or approve the proposed deep blue.
3. Staff placeholders: token colours only (recommended), or leave them untouched.
4. Timetable week view on desktop: a 7-column grid (recommended), or keep the list.
5. Notifications: add "Needs you / All" tabs (client-side), or keep a single list.
6. Dark mode: later (recommended), or now.
7. Tooling: approve `@playwright/test` (and optionally `@axe-core/playwright`), and choose where screenshots go (A or B).
8. Mobbin: skip it, or share screens from your own account.
