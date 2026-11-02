# Public home page — design

Date: 2026-11-02. Status: approved 2026-11-02 (with a static mockup); implemented.

## Intent

Visitors who are not logged in, including people outside AIU, currently land on the login form with no explanation of what UniFlow is. The home page explains what UniFlow does and **how to use it**, then leads AIU students to sign up or log in.

## Goals

- A visitor understands what UniFlow does within the first screen.
- A clear "how to use it" walkthrough, from sign-up to daily use.
- Real screenshots of the app (synthetic data only), so visitors see the product rather than a description of it.
- Sign up and Log in are always one click away.

## Non-goals

- No "how it's built" or technology section, and no GitHub link.
- No video for now (possible later: a short clip recorded with Playwright and the same fake data).
- No backend, API, auth or data changes.

## Anti-goals

- No invented numbers, testimonials, logos, or features the app doesn't have.
- No real student data in any image.
- No new dependencies (no animation or carousel libraries).

## Approach (chosen: A)

| | Option | Trade-off |
|---|---|---|
| **A (chosen)** | `/` shows the home page to logged-out visitors; logged-in users still get "For you" at `/`. | Clean shared address; one routing rule and its tests change. |
| B | Separate `/welcome`; logged-out `/` redirects there. | Code more separate, but a less clean address and logged-in users could still see it. |
| Dropped | A larger login page. | A whole website squeezed next to the login form. |

**Behaviour under A:**
- Logged out, `/` → home page.
- Logged in, `/` → "For you" (onboarding redirect unchanged).
- Logged out, any other private page (e.g. `/timetable`) → `/login?next=…`, as today.
- While the session is still loading, show the existing loading state, so logged-in users never see the home page flash.

## Page content (top to bottom)

1. **Top bar:** wordmark, links to "How it works" and "Features" (in-page anchors), **Log in**, **Sign up**. On phones, the anchors are hidden and only the two buttons remain.
2. **Opening section:** one-sentence promise, a short supporting line, Sign up / Log in buttons, and a screenshot of "For you".
3. **The problem:** students follow many WhatsApp and Telegram groups; deadlines, class changes and messages naming them get buried.
4. **How to use UniFlow** (numbered steps):
   1. Sign up with your `@student.aiu.edu.my` email.
   2. Choose your school, programme and intake.
   3. Add the groups you're in, and add your timetable.
   4. Read what matters on "For you", get alerts, and confirm class changes on your timetable.
5. **Feature tour:** For you, Search, Timetable and class changes, Notifications and the daily digest, each with a screenshot and two or three lines.
6. **Trust:** UniFlow reads only the groups students add; every summary links to the original message; a class change applies only when the student confirms it; link to the privacy notice.
7. **Closing call to action:** Sign up / Log in, plus a note that sign-up needs an AIU student email.
8. **Footer:** wordmark, privacy notice, log in.

## Constraints

- Uses the existing design tokens, the lime and ink brand, the Inter font, the light and dark themes, and the existing UI components.
- Responsive at 390 px (phone) and 1440 px (desktop), with no sideways scrolling.
- WCAG 2.2 AA: one `h1`, logical headings, alt text on every screenshot, visible focus, keyboard-reachable links.
- Lazy-loaded, like the other pages.

## Left to the builder

- Exact wording of headings and copy (plain, short, matching the app's tone).
- Screenshot source: reuse the README screenshots produced by `npm run screens:readme` (synthetic data), copied or generated into the frontend's static files at sensible sizes.
- Visual layout details within the existing visual language.

## Verification

- Router tests: logged-out `/` shows the home page; logged-in `/` shows "For you"; logged-out `/timetable` still goes to login.
- `npm test`, `typecheck`, `lint`, and the Playwright smoke and a11y projects, with the home page added to `e2e/routes.ts`.
- Screenshots at phone and desktop sizes in both themes, checked by eye (up to 3 iterations).
