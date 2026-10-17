# UI/UX page inventory (Phase 1 audit)

Audit date: 2026-10-17. This is the starting point for the redesign. Every route below was found in
[`frontend/src/router.tsx`](../../frontend/src/router.tsx). Every finding was checked against the
code or against the baseline screenshots.

**How to read it**
- **Verified** means it was seen in the code or in a screenshot.
- **Interpretation** means a design judgement.
- **Open** means it still needs an answer.
- **Risk** is how likely a redesign of that page is to break behaviour: Low, Medium or High.

## Baseline evidence

| What | Where | Notes |
|---|---|---|
| Baseline screenshots, 13 routes × 2 viewports | `C:\Users\abdul\Desktop\uniflow-screenshots\before-redesign\{desktop,phone}\` (outside the repo) | Desktop is 1440×900, phone is 390×844, full-page, at 2× scale. Taken 2026-10-17 from the local dev servers (`npm run dev`, Django `runserver`), logged in as the developer's own student account. **These contain real names, so they stay outside the repo and must not be committed.** |
| Frontend tests | `npm test` in `frontend/` | **106 passed** (2026-10-17). `npm run typecheck` and `npm run lint` are clean. |
| Browser tooling | none in the project | Playwright is not a dependency. The baseline was captured with a throwaway `playwright-core` script outside the repo, driving the installed Chrome. |
| Console and network errors during capture | — | Public pages: one expected `400` from the refresh call when logged out. Logged-in pages: none after login. A first attempt that reloaded every page hit the login throttle (`429`, 10 a minute), which is expected behaviour. |

Not captured yet: loading states, error states, empty states (except the digest page), onboarding,
the activation and reset links, the staff area, 403 pages, and the week view of the timetable.
Producing these needs synthetic test data; see the redesign plan's screenshot workflow.

## The app shells

| Shell | File | What it does now (verified) | Issues |
|---|---|---|---|
| Student area | [`components/AppLayout.tsx`](../../frontend/src/components/AppLayout.tsx) | From `md` up: a 240 px white sidebar with text-only links, a red unread badge, the dev-only `API: ok` badge, the user's name, and Profile and Log out buttons. On phones: a sticky top bar (wordmark, Profile link) and a fixed 5-item bottom bar with text-only labels. Pages sit in `max-w-3xl`. | **P1:** at 1440 px the content uses about 1070 of 1200 available px; the right half of the screen is empty (screenshot `desktop/10`). **P2:** nav items have no icons, although `lucide-react` is installed and imported nowhere (0 imports). **P2:** on phones, logging out is only possible from the bottom of the Profile page. **P2:** the unread badge uses raw `bg-red-600`. |
| Auth frame | [`components/AuthLayout.tsx`](../../frontend/src/components/AuthLayout.tsx) | Text wordmark above a centred white card. Used by login, register, privacy, activation, forgot and reset password, and onboarding. | **P2:** the first screen a student sees says nothing about what UniFlow does. The privacy notice is squeezed into a 28 rem card (`desktop/04`). |
| Staff area | [`components/StaffLayout.tsx`](../../frontend/src/components/StaffLayout.tsx) | Dark slate sidebar. Every section is a "Coming soon" placeholder ([`pages/Placeholder`](../../frontend/src/pages/Placeholder/Placeholder.tsx)). | Staff pages are milestone M10 ([PROGRESS.md](../PROGRESS.md)). **Proposed: out of scope**, except keeping the shell visually consistent. |

## Routes

### Public

| Route | Page file | User goal | Data | Key interactions | Verified issues | Risk |
|---|---|---|---|---|---|---|
| `/login` | `pages/Login/Login.tsx` | Get into UniFlow | `POST auth/jwt/create/` via `AuthContext` | Zod validation; `?next=` (only internal paths, `safeNext`); a 401 shows a hint about activation | Plain card with no product context. Buttons are 36 px (`size="lg"` = `h-9`). | **High** (auth) |
| `/register` | `pages/Register/Register.tsx` | Create an account with an `@student.aiu.edu.my` email | `POST auth/users/` | Client domain check; backend field errors mapped under fields; "Check your email" success state | The success state was not captured. Same plain card. | **High** (eligibility rules) |
| `/forgot-password` | `pages/ForgotPassword/` | Get a reset link | Djoser reset | Same reply for unknown emails (backend setting) | — | Medium |
| `/reset-password/:uid/:token` | `pages/ResetPassword/` | Set a new password | Djoser confirm | Token in the URL | Not captured | Medium |
| `/verify-email/:uid/:token` | `pages/ActivateAccount/` | Activate the account | Djoser activation | Runs on load | Not captured | Medium |
| `/privacy` | `pages/Privacy/Privacy.tsx` | Read what UniFlow reads and keeps | static | Linked from register and profile | Long legal text in a narrow card; no headings navigation (`desktop/04`, 1460 px tall) | Low |
| `*` | `pages/NotFound/NotFound.tsx` | Recover from a bad link | — | "Go to home" | Fine, but uses raw `text-brand-600` and `text-slate-600` | Low |

### Student area (logged in, wrapped in `RequireAuth`; students without a profile go to `/onboarding`)

| Route | Page file | User goal | Data (API) | Key interactions | Verified issues | Risk |
|---|---|---|---|---|---|---|
| `/` For you | `pages/ForYou/ForYou.tsx`, `components/TodayBox.tsx`, `components/FeedItemCard.tsx`, `lib/feed.ts` | See what needs me today, by priority | `GET feed/` (list with `tier`), `GET feed/home/` (today's classes, pending changes) | Four tiers in fixed order (Direct attention, Action required, Important updates, Digest); empty tiers hidden; the Today box is students-only; the yellow "N class changes waiting" link goes to `/timetable` | **P1:** every tier uses the same white card; the only difference is a small heading, so "named in this" looks like "good to know". **P1:** the item card shows neither the source group nor when it was posted. The list API has no group field (`types/feed.ts` `FeedItem`); it is only in the detail `evidence`. Showing it would need an **API change, so it is a proposal only**. **P2:** `PageLoading` is a `min-h-screen` "Loading…" text, used inline (11 uses), which pushes the layout around. **P2:** `feed/home/` returns tiered lists and `digest_preview`, but the page uses `feed/` for the tiers and ignores `digest_preview`. | Medium |
| `/insights/:id` | `pages/Insight/Insight.tsx` | Understand one item, trust it, act | `GET feed/{id}/`; `POST` read / dismiss / not_relevant | Opening it **marks it read** (`useEffect`); Dismiss and "Not relevant" navigate to `/`; "Open original" links (`evidence.open_url`); "Open the link"; pending class change → link to timetable | **P1:** the key trust info ("Why you see this", source quotes) is styled as secondary grey text. **P2:** the back link always says "← For you", even when the user came from Search or Notifications. **P2:** the "Official" and "Not confirmed" badges differ only by fill. | **High** (read-marking side effect) |
| `/digest?date=` | `pages/Digest/Digest.tsx` | Skim the day's "good to know" items | `GET feed/digest/` | Grouped by `info_type`; reached only from a digest notification | **P2:** not in the navigation, and For you doesn't link to it either. The empty state was verified (`desktop/15`). | Low |
| `/timetable` (`?view=week&date=`) | `pages/Timetable/Timetable.tsx`, `components/ClassChanges.tsx`, `SectionPicker.tsx`, `AddClassForm.tsx`, `TimetableImport.tsx` | See my classes; confirm or reject AI-detected changes; manage my sections | `timetable/today/`, `week/`, `sections/` (mine, search, join, leave, add), `changes/` (answer), `imports/` (start, poll, choose tab, confirm, discard) | Today / This week toggle (`aria-pressed`); week navigation by URL; a change card with quotes and **Confirm/Reject** (only *my* timetable changes); three toggle panels (import, pick, add); a shared group timetable offer | **P0 (phone): horizontal overflow.** The "My sections" header row (`flex gap-2`, three buttons, no wrap) makes the page 445 px wide on a 390 px screen (`phone/11`, measured width 445). **P1:** the change box comes before the day's classes and takes the first screen (`desktop/11`). **P1:** the three panel buttons look like the selected-state buttons; a panel opens under the list with no heading or close. **P2:** "No classes today" with no hint of the next class. **P2:** "Remove" sits right next to a section with no confirmation; that is current behaviour, keep it but make it visually quieter or safer (decision). | **High** (changes, enrolment, imports) |
| `/sources` "Groups" | `pages/Sources/Sources.tsx` | Add my WhatsApp groups; feed messages by hand | `sources/` (mine, create, connect), paste, upload | Name plus optional invite link (connect vs create); success text; per-group paste/upload panels | **P2:** status ("Waiting for UniFlow to join", "Disconnected") is plain text inside a grey line, with no badge or icon. **P2:** the disabled "Add group" button looks faded (40 % opacity) with no reason given. **P2:** both panel buttons per group are always visible, which is heavy for a list. | Medium |
| `/search?q=` | `pages/Search/Search.tsx` | Find something I was shown before | `GET feed/search/?q=` | At least 2 characters; the query lives in the URL | **P2:** no result count, no recent or suggested queries (would need data, so a proposal only); empty and error states exist | Low |
| `/notifications` | `pages/Notifications/Notifications.tsx`, `lib/notifications.ts` | See alerts; open them | `notifications/`, mark read, mark all read; `unread-count/` polled every 60 s while visible | Clicking marks it read and navigates; "Mark all as read" | **P2:** unread is shown by a tinted background plus a dot (`aria-hidden`) and bold text; the dot has no text alternative on this page (the row's kind label helps). **P2:** no grouping by day. | Medium |
| `/profile` | `pages/Profile/Profile.tsx`, `StudentDetailsForm.tsx`, `PreferencesForm.tsx`, `ChangePasswordForm.tsx` | Fix my studies, interests, nicknames, password | `users/me/` (PATCH), academics lists, preference choices | Four independent forms, each with its own save; semester override; chips are visually hidden checkboxes (`peer sr-only`) | **P1 (phone):** one 2,497 px column (`phone/17`) with no way to jump between sections. **P2:** the full-width "Save interests" button looks the same as the page's main actions. | Medium |
| `/onboarding` | `pages/Onboarding/Onboarding.tsx` | First-time setup: studies, then interests (skippable) | same as profile | 2 steps in local state; staff and finished students are redirected | Not captured (needs a fresh student). No step indicator. | **High** (gate for new users) |

### Staff area (`/staff/*`, `RequireCapability`)

| Route | Status | Note |
|---|---|---|
| `/staff`, `/staff/{announcements,events,documents,applications,communities,timetable,academics,users}` | Placeholders | Verified in `lib/navigation.ts`. Building them is M10. A 403 shows `pages/NoAccess`. |

## Shared building blocks (verified)

- **shadcn/ui primitives** in `components/ui/`: `button`, `badge`, `input`, `label`. That is all of them; there is no card, tabs, dialog, skeleton or toast.
- **UniFlow components:** `EmptyState`, `ErrorState` (`role="alert"`), `PageLoading` (`role="status"`), `FormField`, `SelectField` (native `<select>`), `FeedItemCard`, `TodayBox`, `ClassChanges`, `SectionPicker`, `AddClassForm`, `TimetableImport`, `HealthBadge` (dev only).
- **Tokens** in [`index.css`](../../frontend/src/index.css): shadcn "nova" neutral, with indigo `#4f46e5` as `primary`, a slate-50 page, Geist Variable, and `--radius: 0.625rem`. Dark tokens exist but are never switched on.
- **Raw palette classes bypass the tokens** in 19 files, for example `text-emerald-700` (7×), `text-brand-600` (5×), `border-slate-200` (5×) and `bg-amber-50` (3×). Success, attention and danger have no semantic tokens.
- **Button sizes:** `sm` (28 px, 22 uses), default (32 px) and `lg` (36 px, 14 uses).
  - [docs/05-frontend.md](../05-frontend.md) line 134 promises "44 px tap targets" on mobile.
  - Only the bottom nav meets that (`min-h-11`).
  - WCAG 2.2 AA's minimum is 24 px, so these pass AA, but they miss the project's own goal.

## Open questions

1. Does AIU have official brand colours or a logo UniFlow may (or must not) use?
2. Should the staff placeholders be restyled now, or left until M10?
3. Inspiration sites you sent earlier: none were found in this project's conversation history. Please send them if they exist.
