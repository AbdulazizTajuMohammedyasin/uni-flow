import { defineConfig } from '@playwright/test'

/**
 * Browser checks and screenshots (docs/ui-ux/redesign-plan.md, section 10).
 * - `npm run e2e`: smoke tests (every page loads, no errors, no sideways scrolling)
 * - `npm run screens`: full-page screenshots into ../artifacts/ui/ (git-ignored)
 *
 * The backend is never called: e2e/mock-api.ts answers /api/v1/ with made-up data.
 * Uses the Chrome installed on this computer, so no browser download is needed.
 */
export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  reporter: [['list']],
  outputDir: '../artifacts/ui/test-results',
  use: {
    baseURL: 'http://localhost:5174',
    channel: 'chrome',
    locale: 'en-GB',
    timezoneId: 'Asia/Kuala_Lumpur',
  },
  projects: [
    { name: 'smoke', testMatch: 'smoke.spec.ts' },
    { name: 'screens', testMatch: 'screens.spec.ts' },
  ],
  webServer: {
    // Its own port, so it never clashes with your normal `npm run dev` on 5173.
    command: 'npm run dev -- --port 5174 --strictPort',
    url: 'http://localhost:5174',
    reuseExistingServer: true,
    env: { VITE_API_URL: '/api/v1' }, // same origin: every call is caught by the fake backend
  },
})
