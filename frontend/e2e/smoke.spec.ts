import { expect, test } from '@playwright/test'

import { mockApi, NOW } from './mock-api'
import { screens, smokeWidths } from './routes'

/** Known problems expected to fail until the redesign fixes them (none right now). Playwright
 * reports it when one starts passing, so the list stays honest. */
const KNOWN_OVERFLOW = new Set<string>([])

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

    test('buttons and fields are easy to tap on a phone (44 px)', async ({ page }) => {
      await page.setViewportSize({ width: 390, height: 844 })
      await page.clock.setFixedTime(NOW)
      await mockApi(page, screen.scenario)
      await page.goto(screen.path)
      await expect(page.getByText(screen.ready).first()).toBeVisible()
      // Native checkboxes (inside a bigger label) and text links inside sentences are exempt.
      const small = await page.evaluate(() =>
        [...document.querySelectorAll<HTMLElement>('button, select, input:not([type=checkbox]):not([type=radio]), [role=radio]')]
          .filter((element) => element.offsetWidth > 1 && element.offsetHeight > 1)
          .filter((element) => element.getBoundingClientRect().height < 43.5)
          .map((element) => `${element.tagName.toLowerCase()} "${(element.textContent || element.getAttribute('aria-label') || '').trim().slice(0, 30)}" ${Math.round(element.getBoundingClientRect().height)}px`),
      )
      expect(small).toEqual([])
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
