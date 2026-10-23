# Visual refresh plan (round 2: approved 2026-10-24)

Date: 2026-10-23. Round 1 ([redesign-plan.md](redesign-plan.md), UI-0 to UI-7) fixed the information architecture, responsiveness and accessibility. It is complete and stays the structural baseline. This round changes the **visual identity** only: colour, type, shape, surfaces and a few signature compositions.

Unchanged by this plan: backend, API, routes, auth, data model, hooks, business rules, copy that tests depend on, and the round-1 accessibility guarantees.

## 1. Brief and references

The product owner rejected the round-1 look (deep blue on cool grey, the default shadcn proportions) and supplied three references with extracted style notes:

| Reference | URL | What UniFlow takes | What it leaves |
|---|---|---|---|
| Perk | https://www.perk.com/ | Warm parchment light theme; one electric lime (`#beff50`) as the only chromatic fill; flat surfaces separated by tone, not shadow; pill buttons; large, tightly tracked headings; the "dark island" block for the one thing that must stand out | Marketing-scale section gaps (80–120 px); 28 px card radius everywhere; all-caps eyebrow labels |
| Supabase | https://supabase.com/ | Dark theme: near-black canvas, hairline borders instead of shadows, monochrome UI where green marks only action and emphasis; regular-weight headings (weight 400/500, never bold) | Green on large backgrounds; the single-canvas rule (UniFlow keeps two surface levels) |
| Modal | https://modal.com/ | Rationing: the accent appears on one element per region; tight negative tracking on UI text; status chips filled with the accent only when they mean "active" | The phosphor-green text palette (low readability for long student-facing text); 3D illustrations; a second display typeface |

Common thread: **a neutral, flat, typographic interface with one vivid green-yellow accent that always means something.** Reference images are not saved or committed; only URLs and notes are kept ([reference-research.md](reference-research.md), round 2).

## 2. Baseline

- Screenshots of the current design: `artifacts/ui/v2-baseline/{light,dark}/{phone,laptop,desktop}/` (git-ignored), from the existing harness (`npm run screens`) with synthetic data; no real student data.
- Tests at baseline: `npm test` 127, `npm run e2e` 284 (smoke + accessibility), `typecheck` and `lint` clean.

**What reads as generic today** (observed in the baseline):
1. Deep blue primary + cool grey page: the default "institutional SaaS" combination; no identity.
2. Every surface is a white rounded rectangle with a border; hierarchy comes from headings only.
3. Headings are semibold and conventionally tracked; the type has no voice.
4. The attention style (amber on cream) and the primary (blue) compete: two chromatic accents.
5. The auth screen's left panel is a plain text list; the first screen a student sees is forgettable.

## 3. Direction: "Lime marks what is live"

UniFlow's subject is a feed of things that affect a student *now*: a class moved, a lecturer asking for them, today's timetable. The accent therefore gets one meaning: **lime = live / act here**. It fills primary buttons, marks the current time in the timetable, flags unread items and the active navigation item. Everything else is ink, paper and tone.

The thing that must not be missed ("Needs you": named, action required, a change to confirm) is not another colour. It is a **dark island**: an inverted block (Perk) on the light page, which carries a lime marker. In dark mode it becomes a raised surface with a lime edge.

**Principles**
1. **One accent, one meaning.** Lime never decorates. No second chromatic colour, except red for errors and destructive actions (an accessibility requirement, not a brand colour).
2. **Tone, not shadow.** Paper → white surface → dark island. Shadows only on floating layers (menus, popovers).
3. **Type carries the voice.** One family, two weights (400, 500), tight tracking at heading sizes. No bold, no all-caps labels.
4. **Spend boldness in two places only:** the auth hero (large type on a lime field) and the For you header with the Today rail. Every other page stays quiet.
5. **Round 1 accessibility holds:** 4.5:1 text, 3:1 control edges, status never by colour alone, 44 px phone targets.

## 4. Tokens

Exposed through the existing shadcn variables in `src/index.css`, so components keep using `bg-primary`, `text-muted-foreground`, etc. Contrast values computed (WCAG 2.x formula).

### Light ("parchment")

| Token | Value | Use | Contrast |
|---|---|---|---|
| `--background` | `#f5f5eb` | Page | — |
| `--card` | `#ffffff` | Lists, forms, panels | — |
| `--foreground` | `#14140f` | Text, links (underlined), focus ring | 16.8:1 on page, 18.5:1 on white |
| `--muted-foreground` | `#5c5c52` | Secondary text | 6.2:1 on page, 6.8:1 on white |
| `--border` | `#d2d2c8` | Dividers (decorative) | — |
| `--input` | `#84847a` | Field and checkbox edges | 3.8:1 on white, 3.4:1 on page |
| `--primary` | `#8fcc2e` (lime) | Primary buttons, now-marker, unread dot, active nav | ink on lime 9.5:1 |
| `--primary-foreground` | `#14140f` | Text on lime | — |
| `--island` / `--island-foreground` (new) | `#2a2a24` / `#f5f5eb` | "Needs you" block | 13.2:1; muted `#b8b8ac` 7.2:1; lime on island 12.1:1 |
| `--destructive` | `#b42318` | Errors, destructive actions | 6.6:1 on white |
| `--success` | `#3a6b10` | "Saved", "Added" | 6.4:1 on white |

Lime against the page is 1.1:1, so a lime button's edge is not a visible boundary. WCAG 1.4.11 does not require one when the label identifies the control; the focus ring is ink (16.8:1), never lime, in the light theme.

### Dark ("terminal")

| Token | Value | Contrast |
|---|---|---|
| `--background` | `#121210` | — |
| `--card` | `#1c1c19` | — |
| `--foreground` | `#f2f2ea` | 16.7:1 on page, 15.2:1 on surface |
| `--muted-foreground` | `#a3a398` | 7.4:1 / 6.7:1 |
| `--border` | `#2e2e2a` | decorative |
| `--input` | `#6b6b62` | 3.5:1 on page, 3.2:1 on surface |
| `--primary` | `#8fcc2e`, text `#14140f` | lime on page 9.7:1 (also used as the focus ring) |
| island | `#262622` with a 2 px lime left edge | text 13.5:1 |
| `--destructive` | `#f2877d` | 6.9:1 on surface |
| `--success` | `#9fdc5a` | 10.5:1 on surface |

The same lime in both themes keeps one identity. Its brightness is reduced in dark mode only by area (thin markers, buttons), never by changing the hex.

### Type

- **Geist Variable, already installed; no new dependency.** It is a close free substitute for the references' geometric sans (OTSono, Circular).
- Weights 400 and 500 only (semibold and bold are removed from headings).
- Scale (px): 13 / 14 / 16 (body) / 18 / 22 / 28 / 40, plus 56 for the auth hero only.
- Tracking: −0.02em at 22–28 px, −0.03em at 40 px and above; normal at body sizes.
- `tabular-nums` for times (unchanged).

### Shape, space, motion

| Element | Value |
|---|---|
| Buttons, chips, tabs, nav items | Pill (9999px) |
| Panels and lists | 20px radius |
| Inner elements (rows inside a panel, menus) | 12px |
| Inputs | 10px |
| Shadow | none, except menus and popovers |
| Spacing | 4 px base; page gutter 16 / 24 / 32 px (phone / tablet / desktop); section gap 32–40 px (app, not marketing) |
| Motion | unchanged from round 1: about 150 ms colour and opacity on state changes; none on page load; reduced motion respected |

## 5. Page-by-page changes (presentation only)

| Area | Change |
|---|---|
| **Primitives** (`components/ui/`) | `Button`: default = lime pill with ink text; `outline` = transparent pill with an ink hairline; `ghost` unchanged in behaviour; `destructive` keeps red. `Badge`: pill; "active" status badges filled lime, neutral ones outlined. `Tabs`: pill segmented control on a tonal track. `Input`/`SelectField`: 10 px radius, white field on parchment. Sizes unchanged (44 px on phones). |
| **App shell** | Sidebar on the page colour (no white slab), wordmark set in the heading style, nav items as pills: active = lime fill with ink text **and** weight 500 (not colour alone). Phone bottom nav: active item gets a lime pill behind the icon. Unread count stays a red badge with its text label. |
| **Auth** (`AuthLayout`) | Desktop: the left panel becomes a lime field with the existing tagline "Only the information that matters to you." at 56 px, tight tracking, and the three existing lines below it. Phone: a lime band at the top with the wordmark and tagline at 28 px. The form panel stays white on parchment. Copy unchanged. |
| **For you** | Header: greeting and date in the 28/40 px heading style; the Today rail with the lime now-marker. "Needs you" becomes the dark island, items inside as rows separated by island hairlines. "Updates for you" and "Good to know" as white panels with hairline rows. Unread = lime dot plus the existing hidden "Unread" text. |
| **Item page (Insight)** | Title in the heading style; "Why you see this" and the source byline as a parchment block; "What to do" in the island style when present; "Open original" as an outline pill. |
| **Timetable** | Week grid: class blocks as white 12 px tiles with ink text on the parchment grid; the current-time line in lime; changed classes keep their word + icon badge ("Moved", "Cancelled"). The "changes to confirm" panel uses the island style. "Add classes" chooser: pills. |
| **Groups, Search, Notifications, Digest** | White panels, hairline rows, pill status badges (lime = "Connected", outline = "Waiting to join", red outline = "Disconnected"). Notifications tabs as pills. |
| **Profile, Onboarding** | Section nav as pills; the onboarding step bar in lime. Forms on white panels. |
| **Privacy, 404/403/error, staff placeholders** | Tokens and type only. |

## 6. Accessibility and responsive plan

Unchanged guarantees from round 1, re-run on the new tokens:
- `e2e/a11y.spec.ts`: the 27 measured contrast pairs are updated to the new tokens in both themes (text 4.5:1; edges and focus 3:1), and the island pairs are added.
- Focus ring: ink in light, lime in dark; must show on lime buttons (checked in the keyboard walk).
- Viewports 360 / 390 / 768 / 1024 / 1280 / 1440; no sideways scrolling (smoke).
- Active nav and unread state never by colour alone (weight + text; dot + hidden label).

## 7. Risks and safeguards

| Risk | Safeguard |
|---|---|
| Lime buttons blend into the page (1.1:1 edge) | Labels identify the control; ink focus ring; buttons keep generous padding; checked by eye in screenshots of every page |
| The dark island makes "Needs you" heavier than intended on a busy day | Rows, not cards, inside the island; screenshot review with the `busy` fixture at 390 and 1440 |
| Tests depend on class names or copy | Tests query by role and text, not colour; no copy changes are planned. `npm test`, `typecheck`, `lint` and `npm run e2e` after every milestone |
| Token renames break components | Keep the shadcn variable names; add only `--island`, `--island-foreground`, `--island-muted` |
| Dark mode regressions | Every screenshot run covers both themes |

## 8. Milestones

| # | Milestone | Scope |
|---|---|---|
| V2-1 | Tokens and primitives | `index.css` (both themes), `button`, `badge`, `tabs`, `input`, `SelectField`, contrast pairs in `a11y.spec.ts` |
| V2-2 | App shell | `AppLayout`, `AccountMenu`, bottom nav, `PageHeader`, `StaffLayout` |
| V2-3 | Auth and public pages | `AuthLayout`, login/register/reset/activate, privacy, 404/403 |
| V2-4 | For you, item page, digest | `TodayBox`, `ItemRow`, island block, `Insight`, `Digest` |
| V2-5 | Timetable | `WeekGrid`, `ClassChanges`, section list, import and add flows |
| V2-6 | Groups, Search, Notifications, Profile, Onboarding | Remaining pages |
| V2-7 | Regression pass | Full screenshot set (`artifacts/ui/v2-final/`), keyboard walk, contrast, before/after summary |

Each milestone: at most 3 screenshot iterations (`artifacts/ui/v2-N-iteration-NN/`), then a summary of files changed, checks run and open issues. The product owner commits.

## 9. Acceptance criteria

- No raw colour classes outside `components/ui/` (existing grep check).
- No blue or amber left in either theme (grep for the round-1 hex values returns nothing).
- All contrast pairs in `a11y.spec.ts` pass in both themes.
- `npm test`, `typecheck`, `lint`, `npm run e2e` pass.
- No changes under `backend/`, `src/api/`, `src/context/`, `src/hooks/` or to routes.

## 10. Decisions (2026-10-24)

Made after reviewing three rounds of static mockups (not committed; rendered from synthetic data):

| # | Question | Decision |
|---|---|---|
| 1 | Primary buttons | Lime fill |
| 2 | "Needs you" | Dark island |
| 3 | Accent | Deeper lime `#8fcc2e` instead of `#beff50` (the brighter value was judged too glaring). Ink on it 9.5:1; lime on the island 7.5:1, on the dark page 9.7:1 |
| 4 | Typeface | **Inter** (`@fontsource-variable/inter`, replacing `@fontsource-variable/geist`). A more distinctive face (Bricolage Grotesque) was rejected in favour of a neutral, professional one |
| 5 | Default theme | Follow the device (unchanged) |

Where this document still says `#beff50` or Geist, the decisions above take precedence.
