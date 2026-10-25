import path from 'node:path'

import { expect, test } from '@playwright/test'

import { mockApi, NOW } from './mock-api'
import { screens, viewports } from './routes'

/**
 * Full-page screenshots of every page and state, for reviewing the redesign.
 * Saved to artifacts/ui/<run>/<theme>/<viewport>/<page>.png (git-ignored).
 *   SCREENS_RUN=iteration-01 npm run screens      (default run name: "latest")
 *   SCREENS_THEMES=light npm run screens          (default: light and dark)
 */
const run = process.env.SCREENS_RUN ?? 'latest'
const themes = (process.env.SCREENS_THEMES ?? 'light,dark').split(',') as ('light' | 'dark')[]
const root = path.resolve(import.meta.dirname, '../../artifacts/ui', run)

for (const theme of themes) {
  for (const [device, viewport] of Object.entries(viewports)) {
    test.describe(`${theme} ${device}`, () => {
      test.use({ viewport, colorScheme: theme, deviceScaleFactor: 2 })

      for (const screen of screens) {
        test(screen.name, async ({ page }) => {
          await page.clock.setFixedTime(NOW)
          await mockApi(page, screen.scenario)
          await page.goto(screen.path)
          await expect(page.getByText(screen.ready).first()).toBeVisible()
          await page.evaluate(() => document.fonts.ready)
          if (screen.action === 'open-account-menu') {
            await page.getByRole('button', { name: 'Account menu' }).filter({ visible: true }).click()
            await expect(page.getByRole('menuitem', { name: 'Log out' })).toBeVisible()
          }
          if (screen.action === 'open-needs-you') {
            await page.getByRole('tab', { name: /Needs you/ }).click()
            await expect(page.getByRole('tab', { name: /Needs you/ })).toHaveAttribute('data-state', 'active')
          }
          if (screen.action === 'paste-into-group') {
            await page.getByRole('button', { name: /^Add messages to CCS2213/ }).click()
            await page.getByRole('menuitem', { name: 'Paste messages' }).click()
            await expect(page.getByLabel('Messages', { exact: true })).toBeFocused()
          }
          if (screen.action === 'remove-a-group') {
            await page.getByRole('button', { name: /^Remove CCS2213.* from my groups$/ }).click()
            await expect(page.getByRole('button', { name: 'Remove', exact: true })).toBeVisible()
          }
          await page.screenshot({
            path: path.join(root, theme, device, `${screen.name}.png`),
            fullPage: screen.action !== 'open-account-menu', // an open menu is drawn over the first screen
            animations: 'disabled',
          })
        })
      }
    })
  }
}
