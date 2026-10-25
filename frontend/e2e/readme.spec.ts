import path from 'node:path'

import { expect, test, type Page } from '@playwright/test'

import { mockApi, NOW } from './mock-api'

/**
 * The screenshots shown in the README, with the made-up data of e2e/mock-api.ts.
 * Saved to docs/screenshots/ (committed):  npm run screens:readme
 */
const root = path.resolve(import.meta.dirname, '../../docs/screenshots')

type Shot = {
  name: string
  path: string
  ready: string | RegExp
  device: 'desktop' | 'phone'
  theme?: 'light' | 'dark'
  before?: (page: Page) => Promise<void>
}

const shots: Shot[] = [
  { name: 'for-you', path: '/', ready: 'Project meeting with Dr Farah', device: 'desktop' },
  { name: 'announcement', path: '/insights/103', ready: 'Where it came from', device: 'desktop' },
  { name: 'timetable-week', path: '/timetable?view=week', ready: '19 Oct – 25 Oct', device: 'desktop' },
  { name: 'groups', path: '/sources', ready: 'SCI Student Affairs', device: 'desktop' },
  { name: 'search', path: '/search?q=internship', ready: /internship at a Kuala Lumpur/, device: 'desktop' },
  {
    name: 'notifications-dark',
    path: '/notifications',
    ready: 'Mark all as read',
    device: 'desktop',
    theme: 'dark',
    before: async (page) => {
      await page.getByRole('tab', { name: /Needs you/ }).click()
      await expect(page.getByRole('tab', { name: /Needs you/ })).toHaveAttribute('data-state', 'active')
    },
  },
  { name: 'phone-for-you', path: '/', ready: 'Project meeting with Dr Farah', device: 'phone' },
  { name: 'phone-timetable', path: '/timetable', ready: 'My sections', device: 'phone' },
  { name: 'phone-announcement-dark', path: '/insights/101', ready: 'Where it came from', device: 'phone', theme: 'dark' },
]

const devices = {
  desktop: { viewport: { width: 1440, height: 900 }, deviceScaleFactor: 1 },
  phone: { viewport: { width: 390, height: 844 }, deviceScaleFactor: 2 },
}

for (const shot of shots) {
  test.describe(shot.name, () => {
    test.use({ ...devices[shot.device], colorScheme: shot.theme ?? 'light' })

    test(shot.name, async ({ page }) => {
      await page.clock.setFixedTime(NOW)
      await mockApi(page, 'busy')
      await page.goto(shot.path)
      await expect(page.getByText(shot.ready).first()).toBeVisible()
      await page.evaluate(() => document.fonts.ready)
      await shot.before?.(page)
      await page.screenshot({ path: path.join(root, `${shot.name}.png`), animations: 'disabled' })
    })
  })
}
