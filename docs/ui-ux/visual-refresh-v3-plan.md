# Visual refresh plan (round 3: cobalt on cream, warm stone dark)

Date: 2026-11-07. Status: **awaiting approval**.

Round 1 ([redesign-plan.md](redesign-plan.md)) set the information architecture, responsiveness and accessibility. Round 2 ([visual-refresh-plan.md](visual-refresh-plan.md)) introduced the lime-on-parchment identity. Round 3 replaces the round-2 palette and surfaces. Structure, layout, copy and behaviour are unchanged.

Unchanged by this plan: backend, API, routes, auth, data model, hooks, business rules, copy that tests depend on, and the round-1 accessibility guarantees.

## 1. Problem and decision

**Problem with round 2.** Every neutral token shares the accent's yellow-olive hue: page `#f5f5eb`, text `#14140f`, secondary text `#5c5c52`, borders `#d2d2c8`, dark page `#121210`. With no clean neutral to contrast against, the lime blends into the page, and the interface reads as muddy. Large lime fills (the active nav item, the home and auth panels) and the near-black "island" blocks add weight without adding meaning.

**Decision (product owner, 2026-11-07), after reviewing rendered mockups:**

| Question | Decision |
|---|---|
| Light theme | Palette from [dock.us](https://dock.us/): warm cream canvas, white cards with a feather-light shadow, cool near-black text, one cobalt blue for every action |
| Dark theme | "Warm stone": a brown-black that mirrors the cream canvas, with the **same** cobalt button and white label as the light theme |
| Rejected | A cool blue-black dark theme (inconsistent with the warm light theme); lime on neutral grey; lime or teal on slate |

The mockups were rendered from the project's synthetic screenshot data and are not committed.

**Reference.** Dock (dock.us): cream canvas `#faf9f7`, ink `#121722`, cobalt `#0068f9` as the only filled action colour, violet `#6736eb` for small decorative tags only, pill buttons, 16 px cards, hairline borders and a three-layer micro-shadow. The warm stone dark pairing (`#faf9f7` with `#1c1917`) follows established warm light/dark systems, for example [Convictional's brand colours](https://get.convictional.com/handbook/brand/color/) and the [Grounded Tierra](https://www.obsidianstats.com/themes/obsidian-grounded-tierra) theme.

## 2. Direction: "Blue means act"

- **One accent, one meaning.** Cobalt fills primary buttons, the current class, unread dots and the "Today" marker, and colours links and the active nav icon. Red stays for errors and destructive actions; green only for "Saved" and "Connected".
- **Tone and a light shadow, not slabs.** Cream page → white card (micro-shadow) → soft blue panel for "Needs you" and changes to confirm. The dark island blocks are retired.
- **Violet is decoration only:** the "Official" tag. Never an action or a link.
- **Same type family.** Inter (Dock's own substitute for Roobert) stays, with no new dependency. Page and section headings move from weight 400/500 to 600 to match the reference.

## 3. Tokens

The token names are unchanged, so components keep using `bg-primary`, `text-muted-foreground` and so on. The `island-*` tokens keep their names but now describe the soft blue panel. Three tokens are new: `--link`, `--island-accent` and `--tag`/`--tag-foreground`. Contrast is computed with the WCAG 2.x formula.

### Light

| Token | Value | Use | Contrast |
|---|---|---|---|
| `--background` | `#faf9f7` | Page | — |
| `--card`, `--popover` | `#ffffff` | Lists, panels, forms, menus | — |
| `--foreground` | `#121722` | Text | 17.0 on page, 17.9 on card |
| `--muted-foreground` | `#5f6571` | Secondary text (Dock's `#777c86` is 3.98:1 on cream, so it was darkened) | 5.6 on page, 5.9 on card, 5.2 on muted |
| `--muted`, `--secondary`, `--accent` | `#f2f1ee` | Hover, selected rows, tracks | — |
| `--border` | `#ebe9e4` | Dividers (decorative) | — |
| `--input` | `#8a8f99` | Field and checkbox edges (Dock's hairline is too faint for controls) | 3.3 on card, 3.1 on page |
| `--primary` / `--primary-foreground` | `#0068f9` / `#ffffff` | Buttons, now marker, unread dot | 4.8 |
| `--link` (new) | `#0068f9` | Links and blue labels | 4.8 on card, 4.6 on page |
| `--ring` | `#0068f9` | Focus ring (now blue in both themes, previously ink) | 4.8 on card, 4.6 on page, 4.4 on the blue panel |
| `--island` / `--island-foreground` | `#eef4ff` / `#121722` | "Needs you", changes to confirm | 16.2 |
| `--island-muted` | `#5f6571` | Hints inside the panel | 5.3 |
| `--island-accent` (new) | `#024bb1` | Section labels and icons inside the panel (cobalt is 4.37:1 there) | 7.2 |
| `--island-border` (new) | `#d6e4f1` | Panel edge (decorative) | — |
| `--attention` / `-foreground` / `-border` | `#eef4ff` / `#024bb1` / `#0068f9` | Pending-change badges | 7.2 |
| `--tag` / `--tag-foreground` (new) | `#f4f0ff` / `#6736eb` | "Official" tag | 5.7 |
| `--destructive` | `#b42318` (unchanged) | Errors, unread count | 6.6 on card |
| `--success` | `#046645` | "Saved", "Connected" | 7.0 on card |
| `--hero-from` / `--hero-to` (new) | `#e3efff` / `#efe9ff` | Gradient wash at the foot of the home and auth hero | — |

### Dark ("warm stone")

| Token | Value | Contrast |
|---|---|---|
| `--background` | `#1c1917` | — |
| `--card`, `--popover` | `#262320` | — |
| `--foreground` | `#f5f3ef` | 15.8 on page, 14.1 on card |
| `--muted-foreground` | `#a8a29e` | 6.9 on page, 6.2 on card, 5.6 on muted |
| `--muted`, `--secondary`, `--accent` | `#2f2b27` | — |
| `--border` | `#35302c` | decorative |
| `--input` | `#78716c` | 3.3 on card, 3.7 on page |
| `--primary` / `--primary-foreground` | `#0068f9` / `#ffffff` (same as light) | 4.8; the button edge on the page is 3.6 |
| `--link` | `#78adff` (cobalt is 3.2:1 as text on the card, so links get a lighter blue) | 6.9 on card |
| `--ring` | `#78adff` | 6.9 on card, 7.7 on page, 6.1 on panel |
| `--island` / `-foreground` / `-muted` | `#212d3e` / `#f5f3ef` / `#a8a29e` | 12.6 / 5.5 |
| `--island-accent` / `--island-border` | `#8fbcff` / `#193b6c` | 7.2 / decorative |
| `--attention` / `-foreground` / `-border` | `#212d3e` / `#8fbcff` / `#78adff` | 7.2 |
| `--tag` / `--tag-foreground` | `#2c2540` / `#b9a3ff` | 6.7 |
| `--destructive` / `-foreground` | `#f2877d` / `#2a0b08` (unchanged) | 6.4 on card / 7.4 |
| `--success` | `#5fcf8f` | 8.0 on card |
| `--hero-from` / `--hero-to` | `#1e2738` / `#262236` | — |

### Shape and elevation

| Element | Round 2 | Round 3 |
|---|---|---|
| Buttons, chips, nav items | Pill | Pill (unchanged) |
| Panels and lists | 20 px, flat | 16 px, micro-shadow (`0 1px 1px rgb(0 0 0/.07)` plus a 0.5 px inset edge) in light; a 1 px border in dark |
| Active nav item | Lime fill | White pill with the micro-shadow, a blue icon and weight 600 (light); a `--muted` pill (dark). The active state is never conveyed by colour alone. |
| Headings | Weight 400–500 | Weight 600, same sizes and tracking |

## 4. Changes by area (presentation only)

| Area | Change |
|---|---|
| **Tokens** (`src/index.css`) | Both themes replaced as in section 3; new tokens registered in `@theme`; the `island` utility becomes the soft blue panel with `--island-border` (no inverted block, no lime edge in dark) |
| **Primitives** (`components/ui/`) | `Button`: default = cobalt with a white label and a darker hover (`#024bb1` light); focus ring uses `--ring`. `Badge`: an `official` variant using `--tag`. Cards: radius and micro-shadow. Sizes unchanged (44 px targets on phones). |
| **App shell** (`AppLayout`, `StaffLayout`, `PageHeader`) | Active nav item as described above; the phone bottom bar gets a light-blue pill behind the active icon; heading weight |
| **For you, item page** (`ForYou`, `ItemRow`, `TodayBox`, `Insight`) | "Needs you" and "What to do" use the blue panel; section labels and icons inside it use `--island-accent`; the ink ring around unread dots (needed only for lime) is removed; "Official" uses the tag badge; text links use `--link` |
| **Timetable** (`Timetable`, `WeekGrid`, `ClassChanges`) | The current class is a cobalt tile with white text; pending changes keep the dashed outline; the change banner and "Changes to confirm" use the blue panel |
| **Auth** (`AuthLayout`) | The lime panel and phone band become a cream panel with the hero gradient wash and ink text; copy unchanged |
| **Home** (`Home`) | The lime header and hero become a white top bar and a cream hero fading into `--hero-from`/`--hero-to`; the dark "problem" block becomes a white card; the closing lime band becomes the gradient wash with a cobalt button. The lime-specific button styles (`inkButton`, `inkOutline`, `onLimeFocus`) are removed in favour of the standard button variants |
| **Groups, Search, Notifications, Digest, Profile, Onboarding, Privacy, error pages** | Tokens only; check text links for `--link` |
| **Screenshots** | `docs/screenshots/` (README) and `src/assets/home/` (home page images) are recaptured with the existing harness (`npm run screens:readme` and the home captures) |

## 5. Accessibility

- `e2e/a11y.spec.ts` contrast pairs are updated: the lime-specific pairs (`--primary` on `--island`, ink on 25 % lime) are replaced with `--link` on page and card, `--island-accent` and `--ring` on `--island`, `--tag-foreground` on `--tag`, and `--primary` against `--background` (button edge, 3:1). Both themes.
- Focus ring: blue in both themes, checked on blue buttons (offset ring) in the keyboard walk.
- Status is never conveyed by colour alone: unread = dot plus hidden "Unread" text; active nav = weight plus pill; changes = word plus icon (unchanged).
- Viewports 360 / 390 / 768 / 1024 / 1280 / 1440; no horizontal scrolling (existing smoke tests).

## 6. Milestones

Each milestone is one reviewable change. The product owner commits.

| # | Milestone | Files |
|---|---|---|
| V3-1 | Tokens, primitives and contrast tests | `index.css`, `components/ui/button.tsx`, `badge.tsx`, `e2e/a11y.spec.ts` |
| V3-2 | App shell | `AppLayout`, `StaffLayout`, `PageHeader`, `HealthBadge` |
| V3-3 | For you, item page and timetable | `ForYou`, `ItemRow`, `TodayBox`, `Insight`, `Timetable`, `WeekGrid`, `ClassChanges` |
| V3-4 | Auth and home page | `AuthLayout`, `Home` |
| V3-5 | Home page layout (added 2026-11-08 at the product owner's request, from an approved mockup) | `Home`, `index.css` (`--phone-frame`, `cta-corner`, `stage-wash`, `phone-glow`), `e2e/readme.spec.ts`, `src/assets/home/` |
| V3-6 | Remaining pages, screenshots and regression pass | Link colour sweep; recapture `docs/screenshots/` (done early in V3-5); full screenshot set in `artifacts/ui/v3-final/` (git-ignored) |

Per milestone: at most 3 screenshot iterations (`artifacts/ui/v3-N-iteration-NN/`, both themes, 390 and 1440 px), then a summary of files changed, checks run and open issues.

## 7. Risks

| Risk | Safeguard |
|---|---|
| `text-primary` used as text in dark mode fails contrast (3.2:1) | New `--link` token; every `text-primary` text use is moved to `text-link` (icons may stay, at 3:1) |
| Lime-specific code left behind (ink rings, `onLimeFocus`) | Grep for `lime`, `island-muted`, `primary-foreground` used as a fill, and the round-2 hex values before V3-5 |
| The soft panel makes "Needs you" too quiet | Screenshot review with the `busy` fixture at 390 and 1440 px; fallback: a 1 px `--island-border` at full cobalt |
| Tests depend on class names or copy | Tests query by role and text; no copy changes |
| Hard-coded colour in `Home.tsx` (one shadow) | Moved to a token |

## 8. Checks and acceptance criteria

- `npm test`, `npm run typecheck`, `npm run lint` and `npm run e2e` (smoke and accessibility) pass after every milestone.
- All contrast pairs in `a11y.spec.ts` pass in both themes.
- No round-2 hex values (`#8fcc2e`, `#f5f5eb`, `#14140f`, `#121210`) remain in `src/`.
- No raw colour classes outside `components/ui/` and `index.css`.
- No changes under `backend/`, `src/api/`, `src/context/`, `src/hooks/` or to routes.

## 9. Out of scope

- The favicon is still Vite's default (`public/favicon.svg`). Replacing it with a UniFlow mark is a separate change.
- Layout, navigation structure, copy and new features.
