# Reference research (Phase 1)

Captured 2026-10-17 with ordinary browser access: a headless Chrome page load plus `WebFetch`. No MCP server was used. The SaaSUI and Refero pages advertise MCP; it was not used.

Reference screenshots were saved **outside the repo**, in the session's temporary folder. They are third-party product images and must not be committed. Only URLs and notes are kept here.

## Source access

| Library | What was reachable without an account | Used? |
|---|---|---|
| **Refero** (https://refero.design/) | The home page, plus `https://refero.design/web-apps` with its category list (Education, Productivity, Scheduling Tools, …). Opening a category showed **only loading placeholders**; screens need an account. | Category list only. No screens were studied, and no paywall or login was bypassed. |
| **SaaSUI** (https://www.saasui.design/) | Public pattern pages with real product screenshots (`/pattern/{type}/{product}`). | **Main source.** |
| **Mobbin** (https://mobbin.com/) | The marketing and explore landing page. Per its own page, screens, flows and search need a free or paid account. | Not used. Needs your decision: sign up yourself and share links, or skip it. |
| Dribbble | Not visited | Optional; visual exploration only. |
| Your earlier inspiration sites | **Not found** in this project's saved conversations | Please send them, if any. |

**Limitation:** SaaSUI shows each product screen at reduced size on its pages. The notes below cover layout, hierarchy and pattern. Exact sizes and colours were not measured.

## Shortlist

### Overall product references (2)

**1. Linear: dashboard, search and filters**
- Viewed at https://www.saasui.design/pattern/dashboard/linear and `/pattern/search/linear`, desktop.
- **Observed:**
  - A narrow light sidebar with small icon + label rows: Inbox, My issues, Views, Roadmaps.
  - Team sections are nested under a muted group label.
  - The main area has a compact header with segmented tabs (All / Backlog / Active / Closed) and a "+ Filter" button.
  - The filter menu lists properties with an icon each.
  - Dense, quiet, almost monochrome, with colour only on status dots.
- **Solves for UniFlow:**
  - A sidebar with icons and grouping instead of five bare text links.
  - Segmented tabs for Today / Week and for notification filters.
  - Colour reserved for status.
- **Adapt, don't copy:**
  - UniFlow's users are students on phones, not power users, so it needs larger targets and less density.
  - No command palette or keyboard-first assumptions.
- **Drawback:** too dense for a first-time student, and the monochrome look could feel cold.

**2. Slite: notifications split by need**
- Viewed at https://www.saasui.design/pattern/notification/slite, a desktop popover.
- **Observed:**
  - The notifications panel has two segments: **"Where you're needed"** and **"Nice to see"**.
  - It has a friendly empty state ("All quiet for now / New notifications will appear here").
  - A dismissible footer offers Slack delivery.
- **Solves for UniFlow:** this is UniFlow's core idea in two words. The four tiers could read as "Needs you" (direct + action + changes to confirm) versus "Good to know" (important + digest), on For you and on Notifications.
- **Adapt:**
  - Keep UniFlow's four backend tiers.
  - The two-way split is only a grouping in the UI, with no API change.
- **Drawback:** a popover pattern; UniFlow uses full pages, especially on phones.

### Page-specific references

| Reference (URL, viewport) | Observed | UniFlow page / problem | Adapt rather than copy | Drawback |
|---|---|---|---|---|
| **Sunsama calendar**, https://www.saasui.design/pattern/calendar/sunsama (desktop) | Day columns (Thursday, Friday, Saturday) with dates; a vertical hour grid on the right with a red **current-time line**; tasks as compact blocks with durations | Timetable week view on desktop; the "now" marker for Today | Use a light theme; use the now-line only on Today; keep the phone list layout | Dark theme; built for time-blocking, not fixed classes |
| **Cal.com event types and availability**, https://www.saasui.design/pattern/calendar/cal-com (desktop) | A list of rows, each with title, slug and duration chip, with actions (toggle, copy, more) aligned right; a settings page with a left sub-nav where every item has a one-line description | Timetable "My sections" list (aligned row actions); Profile as sections with a sub-nav | Fewer actions per row (UniFlow only has Remove); the sub-nav becomes in-page anchors on phones | Admin-flavoured |
| **Claude settings**, https://www.saasui.design/pattern/settings/claude (desktop modal) | A left list of sections with icons; the right pane has small headed groups (Appearance, Voice, Notifications); each control row has a label and a muted one-line explanation | Profile: grouping, plus explanations next to each setting (nicknames, semester override) | A page, not a modal | Very small type in a modal |
| **productboard inbox**, https://www.saasui.design/pattern/notification/productboard (desktop) | Inbox list grouped by time ("THIS MONTH"), unread rows marked with a coloured dot, sender and source on the first line, a detail pane on the right | Notifications grouping by day; For you item cards showing **where** an item came from | Day groups without all-caps labels; master-detail **is not proposed** (it would change routing) | Busy; onboarding overlays |
| **Attio activity panel**, https://www.saasui.design/pattern/notification/attio (desktop) | A panel with tabs "Notifications (0) / Requests (0)" showing counts; a centred empty state explaining *when* you'll be notified, with a link to settings | Notifications and digest empty states: say when something will appear and link to Profile → interests | — | — |
| **Linear login**, https://www.saasui.design/pattern/login/linear (desktop) | A single focused message, "Check your email", with the address in bold and a back link | Register success and Forgot password confirmation states | UniFlow keeps email + password (no magic link; auth must not change) | Dark |
| **Reclaim upcoming list**, https://www.saasui.design/pattern/calendar/reclaim (desktop) | A table of upcoming items: start time, duration, title, status | Possibly "This week" as a compact list on tablets | Not shortlisted for the main design | Dated look |

Looked at and **rejected**:
- Beamer (`/pattern/notification/beamer`) shows an onboarding checklist, not a notification centre.
- The Refero home page has no product screens without an account.

## How the references map to pages

| UniFlow page | References |
|---|---|
| App shell | Linear (icon sidebar, quiet chrome) |
| For you | Slite ("Needs you" vs "Good to know"), productboard (source line on items) |
| Insight detail | productboard (source and sender first), Attio (explaining "why") |
| Timetable | Sunsama (week columns, now-line), Cal.com (row actions in My sections) |
| Notifications | Slite (split), productboard (day grouping, unread dot), Attio (empty state) |
| Search | Linear (compact result rows, filter chips; filters would be client-side only, as a proposal) |
| Profile and onboarding | Claude and Cal.com settings (section nav, explanations next to controls) |
| Auth | Linear (focused confirmation states) |

## What the skills said

- **Frontend Design** ([`.claude/skills/frontend-design/SKILL.md`](../../.claude/skills/frontend-design/SKILL.md)):
  - Ground the design in the subject.
  - Spend boldness in one place.
  - Avoid templated tells: the cream + terracotta look, the "SaaS-card kit" of identical rounded cards with soft shadows, ALL-CAPS eyebrows, and "→" in every link.
  - The current UI is close to that card kit: every section is `rounded-2xl bg-card shadow-sm ring-1`.
- **UI/UX Pro Max** ([`.claude/skills/ui-ux-pro-max/SKILL.md`](../../.claude/skills/ui-ux-pro-max/SKILL.md), local search run 2026-10-17):
  - It recommended the "Minimalism & Swiss" style for productivity tools. **Adopted.**
  - It recommended a teal and orange palette with Plus Jakarta Sans. **Not adopted:** it is a generic match, the font is a new dependency, and black text on teal is a weak pairing.
  - It recommended a landing-page pattern with GSAP motion. **Rejected:** UniFlow is an app, not a marketing page, and GSAP is a new dependency.
  - UX rules **adopted**: don't use colour alone for status; WCAG 2.2 target size (24 px minimum on the web, 44 px for touch); stable loading placeholders with `aria-busy`; predictable Back behaviour; fixed nav must not cover content.
  - Its shadcn stack guidance says to use the shadcn `Sidebar` component. **Deferred:** it brings provider state and more code. The current layout is fine structurally; it only needs restyling.
