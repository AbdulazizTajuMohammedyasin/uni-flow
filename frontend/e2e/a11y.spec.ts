import { expect, test, type Page } from '@playwright/test'

import { mockApi, NOW } from './mock-api'
import { screens } from './routes'

/**
 * Accessibility checks we can make without extra libraries (docs/ui-ux/redesign-plan.md, section 11).
 * They run with the smoke tests: `npm run e2e`.
 */

async function open(page: Page, screen: (typeof screens)[number]) {
  await page.clock.setFixedTime(NOW)
  await mockApi(page, screen.scenario)
  await page.goto(screen.path)
  await expect(page.getByText(screen.ready).first()).toBeVisible()
}

/** Lines of Playwright's accessibility tree for controls that have no name, e.g. `- button`. */
const NAMELESS = /^\s*- (button|link|textbox|searchbox|combobox|checkbox|radio|tab|menuitem|switch|spinbutton)( \[[^\]]*\])*:?\s*$/

for (const screen of screens) {
  test.describe(screen.name, () => {
    test('has one h1, one main, and every control has a name', async ({ page }) => {
      await page.setViewportSize({ width: 1440, height: 1000 })
      await open(page, screen)
      await expect(page.locator('h1:visible')).toHaveCount(1)
      await expect(page.getByRole('main')).toHaveCount(1)
      const tree = await page.locator('body').ariaSnapshot()
      expect(tree.split('\n').filter((line) => NAMELESS.test(line))).toEqual([])
    })

    test('the keyboard reaches everything, and focus is always visible', async ({ page }) => {
      await page.setViewportSize({ width: 1440, height: 1000 })
      await open(page, screen)
      const problems: string[] = []
      const seen: string[] = []
      for (let stop = 0; stop < 60; stop++) {
        await page.keyboard.press('Tab')
        const focus = await page.evaluate(() => {
          const focused = document.activeElement as HTMLElement | null
          if (!focused || focused === document.body) return null
          // A hidden checkbox styled as a chip shows its focus on the chip next to it.
          const tiny = focused.getBoundingClientRect().width <= 1
          const element = (tiny && focused.nextElementSibling instanceof HTMLElement ? focused.nextElementSibling : focused)
          const style = getComputedStyle(element)
          const rect = element.getBoundingClientRect()
          const label = `${focused.tagName.toLowerCase()} "${(element.textContent || element.getAttribute('aria-label') || '').trim().slice(0, 30)}"`
          const ring = (style.outlineStyle !== 'none' && parseFloat(style.outlineWidth) > 0) || style.boxShadow !== 'none'
          const onScreen = rect.width > 1 && rect.height > 1 && rect.bottom > 0 && rect.top < innerHeight
          return { label, key: `${label}@${Math.round(rect.top + scrollY)},${Math.round(rect.left)}`, ring, onScreen }
        })
        if (!focus) break // tabbed past the last control, back to the page
        if (seen.includes(focus.key)) break // went round once
        seen.push(focus.key)
        if (!focus.ring) problems.push(`no focus ring: ${focus.label}`)
        if (!focus.onScreen) problems.push(`focused but not visible: ${focus.label}`)
      }
      expect(problems).toEqual([])
    })
  })
}

test.describe('app frame', () => {
  test('a "Skip to content" link comes first and moves focus to the page', async ({ page }) => {
    await page.setViewportSize({ width: 1440, height: 1000 })
    await open(page, screens.find((screen) => screen.name === 'for-you--busy')!)
    await page.keyboard.press('Tab')
    const skip = page.getByRole('link', { name: 'Skip to content' })
    await expect(skip).toBeFocused()
    await expect(skip).toBeInViewport()
    await page.keyboard.press('Enter')
    await expect(page.getByRole('main')).toBeFocused()
  })

  test('on a phone, For you shows the Today box and the first "Needs you" item without scrolling', async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 })
    await open(page, screens.find((screen) => screen.name === 'for-you--busy')!)
    await expect(page.getByRole('region', { name: 'Today' })).toBeInViewport()
    await expect(page.getByRole('heading', { name: /Needs you/ })).toBeInViewport()
    const firstNeedsYou = page.locator('h2:has-text("Needs you") ~ section').first().getByRole('link').first()
    await expect(firstNeedsYou).toBeInViewport({ ratio: 1 })
  })

  test('animations are switched off when the device asks for less motion', async ({ page }) => {
    await page.emulateMedia({ reducedMotion: 'reduce' })
    await open(page, screens.find((screen) => screen.name === 'for-you--loading')!)
    const skeleton = page.locator('[data-slot="skeleton"]').first()
    await expect(skeleton).toBeVisible()
    const seconds = await skeleton.evaluate((element) => parseFloat(getComputedStyle(element).animationDuration))
    expect(seconds).toBeLessThan(0.01)
    // Everything else too (the global rule in index.css): buttons' colour transitions.
    const button = await page.getByRole('button').first().evaluate((element) => parseFloat(getComputedStyle(element).transitionDuration))
    expect(button).toBeLessThan(0.01)
  })
})

/** Text pairs need 4.5:1; control edges and focus rings need 3:1 (WCAG 2.2 AA, 1.4.3 and 1.4.11).
 * `over` draws the colour at `alpha` over that background first, like `bg-primary/10` on a card. */
const PAIRS: { text: string; on: string; over?: string; alpha?: number; min: number }[] = [
  { text: '--foreground', on: '--background', min: 4.5 },
  { text: '--foreground', on: '--card', min: 4.5 },
  { text: '--muted-foreground', on: '--background', min: 4.5 },
  { text: '--muted-foreground', on: '--card', min: 4.5 },
  { text: '--muted-foreground', on: '--muted', min: 4.5 },
  { text: '--muted-foreground', on: '--accent', over: '--card', alpha: 0.5, min: 4.5 }, // unread alert rows
  { text: '--primary', on: '--background', min: 4.5 },
  { text: '--primary', on: '--card', min: 4.5 },
  { text: '--primary', on: '--accent', over: '--card', alpha: 0.5, min: 4.5 }, // "New" on unread rows
  { text: '--primary', on: '--primary', over: '--card', alpha: 0.1, min: 4.5 }, // icons in a blue circle
  { text: '--primary-foreground', on: '--primary', min: 4.5 },
  { text: '--accent-foreground', on: '--accent', min: 4.5 },
  { text: '--secondary-foreground', on: '--secondary', min: 4.5 },
  { text: '--destructive', on: '--card', min: 4.5 },
  { text: '--destructive', on: '--background', min: 4.5 },
  { text: '--destructive', on: '--destructive', over: '--card', alpha: 0.1, min: 4.5 }, // "Disconnected" badge
  { text: '--destructive-foreground', on: '--destructive', min: 4.5 },
  { text: '--attention-foreground', on: '--attention', min: 4.5 },
  { text: '--success', on: '--card', min: 4.5 },
  { text: '--success', on: '--background', min: 4.5 },
  { text: '--success', on: '--success', over: '--card', alpha: 0.1, min: 4.5 }, // "Connected" badge
  { text: '--sidebar-foreground', on: '--sidebar', min: 4.5 },
  { text: '--input', on: '--card', min: 3 },
  { text: '--input', on: '--background', min: 3 },
  { text: '--ring', on: '--card', min: 3 },
  { text: '--ring', on: '--background', min: 3 },
  { text: '--primary', on: '--card', min: 3 }, // the edge of a filled button
]

for (const theme of ['light', 'dark'] as const) {
  test(`colour contrast of the ${theme} theme`, async ({ page }) => {
    await page.emulateMedia({ colorScheme: theme })
    await open(page, screens.find((screen) => screen.name === 'login')!)
    const failures = await page.evaluate((pairs) => {
      const root = getComputedStyle(document.documentElement)
      const canvas = document.createElement('canvas')
      const context = canvas.getContext('2d', { willReadFrequently: true })!
      // Lets the browser turn any CSS colour into RGB, blending it over a background if asked.
      const rgb = (token: string, over?: string, alpha = 1) => {
        context.globalAlpha = 1
        context.fillStyle = over ? root.getPropertyValue(over).trim() : '#000'
        context.fillRect(0, 0, 1, 1)
        context.globalAlpha = alpha
        context.fillStyle = root.getPropertyValue(token).trim()
        context.fillRect(0, 0, 1, 1)
        return [...context.getImageData(0, 0, 1, 1).data.slice(0, 3)]
      }
      const luminance = (colour: number[]) => {
        const [r, g, b] = colour.map((value) => {
          const channel = value / 255
          return channel <= 0.04045 ? channel / 12.92 : ((channel + 0.055) / 1.055) ** 2.4
        })
        return 0.2126 * r + 0.7152 * g + 0.0722 * b
      }
      return pairs
        .map((pair) => {
          const a = luminance(rgb(pair.text, pair.over ?? pair.on))
          const b = luminance(pair.over ? rgb(pair.on, pair.over, pair.alpha) : rgb(pair.on))
          const ratio = (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05)
          return { ...pair, ratio: Math.round(ratio * 100) / 100 }
        })
        .filter((pair) => pair.ratio < pair.min)
        .map((pair) => `${pair.text} on ${pair.alpha ? `${pair.on}/${pair.alpha * 100} over ${pair.over}` : pair.on}: ${pair.ratio}:1 (needs ${pair.min})`)
    }, PAIRS)
    expect(failures).toEqual([])
  })
}
