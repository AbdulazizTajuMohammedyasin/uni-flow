import { useSyncExternalStore } from 'react'

/** True while the screen matches `query`, e.g. "(min-width: 1280px)". False where the browser
 * can't tell (tests), so pages fall back to their phone layout. */
export function useMediaQuery(query: string): boolean {
  return useSyncExternalStore(
    (onChange) => {
      const media = window.matchMedia?.(query)
      media?.addEventListener('change', onChange)
      return () => media?.removeEventListener('change', onChange)
    },
    () => window.matchMedia?.(query).matches ?? false,
    () => false,
  )
}
