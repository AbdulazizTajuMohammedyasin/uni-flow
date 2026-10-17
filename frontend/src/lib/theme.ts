/**
 * Light / dark theme. "system" (the default) follows the phone or computer setting.
 *
 * The choice is kept in localStorage under "uniflow-theme": the only thing UniFlow keeps there
 * (it is not sensitive; login tokens are never stored in the browser). index.html applies the
 * same rule before the first paint, so a dark-mode user never sees a white flash.
 */
export type Theme = 'light' | 'dark' | 'system'

const KEY = 'uniflow-theme'
const listeners = new Set<() => void>()

function systemPrefersDark(): boolean {
  return window.matchMedia?.('(prefers-color-scheme: dark)').matches ?? false
}

/** The saved choice ("system" when nothing is saved or storage is blocked). */
export function getTheme(): Theme {
  try {
    const saved = localStorage.getItem(KEY)
    return saved === 'light' || saved === 'dark' ? saved : 'system'
  } catch {
    return 'system'
  }
}

/** Puts `.dark` on <html> when the theme (or the system, for "system") is dark. */
export function applyTheme(theme: Theme = getTheme()): void {
  const dark = theme === 'dark' || (theme === 'system' && systemPrefersDark())
  document.documentElement.classList.toggle('dark', dark)
}

export function setTheme(theme: Theme): void {
  try {
    if (theme === 'system') localStorage.removeItem(KEY)
    else localStorage.setItem(KEY, theme)
  } catch {
    // Storage blocked (private mode): the choice still applies until the page is reloaded.
  }
  applyTheme(theme)
  listeners.forEach((listener) => listener())
}

/** For useSyncExternalStore: called whenever the choice changes. */
export function subscribeTheme(listener: () => void): () => void {
  listeners.add(listener)
  return () => listeners.delete(listener)
}

/** Re-applies "system" when the phone or computer switches between light and dark. */
export function followSystemTheme(): () => void {
  const media = window.matchMedia?.('(prefers-color-scheme: dark)')
  if (!media) return () => {}
  const onChange = () => {
    if (getTheme() === 'system') applyTheme('system')
  }
  media.addEventListener('change', onChange)
  return () => media.removeEventListener('change', onChange)
}
