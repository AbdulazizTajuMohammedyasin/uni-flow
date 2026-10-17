import { expect, test } from '@playwright/test'

import { mockApi, NOW } from './mock-api'
import { screens, smokeWidths } from './routes'

/**
 * Problems already known from the Phase 1 audit (docs/ui-ux/page-inventory.md). They are
 * expected to fail until the redesign fixes them; Playwright reports it if one starts passing.
 */
const KNOWN_OVERFLOW = new Set(
  ['timetable-today--busy', 'timetable-week--busy', 'timetable--empty'].flatMap((name) => [`${name}:360`, `${name}:390`]),
)

for (const screen of screens) {
  test.describe(screen.name, () => {
    test('loads without errors', async ({ page }) => {
      const errors: string[] = []
      page.on('pageerror', (error) => errors.push(error.message))
      page.on('console', (message) => {
        // The browser logs every failed request. Those are expected when the fake backend
        // fails on purpose (a visitor's 401, the "error" scenario's 500s); anything else counts.
        const expected =
          message.text().startsWith('Failed to load resource') &&
          (screen.scenario === 'visitor' || screen.scenario === 'error')
        if (message.type() === 'error' && !expected) errors.push(message.text())
      })
      await page.clock.setFixedTime(NOW)
      await mockApi(page, screen.scenario)
      await page.goto(screen.path)
      await expect(page.getByText(screen.ready).first()).toBeVisible()
      expect(errors).toEqual([])
    })

    for (const width of smokeWidths) {
      test(`no sideways scrolling at ${width}px`, async ({ page }) => {
        test.fail(KNOWN_OVERFLOW.has(`${screen.name}:${width}`), 'Known P0 from the audit')
        await page.setViewportSize({ width, height: 900 })
        await page.clock.setFixedTime(NOW)
        await mockApi(page, screen.scenario)
        await page.goto(screen.path)
        await expect(page.getByText(screen.ready).first()).toBeVisible()
        const overflow = await page.evaluate(
          () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
        )
        expect(overflow, 'page is wider than the screen').toBeLessThanOrEqual(0)
      })
    }
  })
}
