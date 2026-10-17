import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { applyTheme, followSystemTheme, getTheme, setTheme } from './theme'

let systemDark = false
const changeListeners = new Set<() => void>()

beforeEach(() => {
  systemDark = false
  changeListeners.clear()
  localStorage.clear()
  document.documentElement.classList.remove('dark')
  vi.stubGlobal('matchMedia', () => ({
    get matches() {
      return systemDark
    },
    addEventListener: (_: string, listener: () => void) => changeListeners.add(listener),
    removeEventListener: (_: string, listener: () => void) => changeListeners.delete(listener),
  }))
})

afterEach(() => {
  vi.unstubAllGlobals()
})

const isDark = () => document.documentElement.classList.contains('dark')

describe('theme', () => {
  it('follows the system by default', () => {
    expect(getTheme()).toBe('system')
    applyTheme()
    expect(isDark()).toBe(false)

    systemDark = true
    applyTheme()
    expect(isDark()).toBe(true)
  })

  it('remembers a chosen theme, whatever the system says', () => {
    systemDark = true
    setTheme('light')
    expect(getTheme()).toBe('light')
    expect(localStorage.getItem('uniflow-theme')).toBe('light')
    expect(isDark()).toBe(false)

    setTheme('dark')
    expect(isDark()).toBe(true)
  })

  it('forgets the choice when going back to "system"', () => {
    setTheme('dark')
    setTheme('system')
    expect(localStorage.getItem('uniflow-theme')).toBeNull()
    expect(isDark()).toBe(false)
  })

  it('switches with the system only while "system" is chosen', () => {
    const stop = followSystemTheme()
    systemDark = true
    changeListeners.forEach((listener) => listener())
    expect(isDark()).toBe(true)

    setTheme('light')
    changeListeners.forEach((listener) => listener())
    expect(isDark()).toBe(false)
    stop()
  })
})
