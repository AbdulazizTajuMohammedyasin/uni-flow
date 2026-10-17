import { useSyncExternalStore } from 'react'

import { getTheme, setTheme, subscribeTheme, type Theme } from '@/lib/theme'

/** The chosen theme ("light", "dark" or "system") and a function to change it. */
export function useTheme(): [Theme, (theme: Theme) => void] {
  const theme = useSyncExternalStore(subscribeTheme, getTheme)
  return [theme, setTheme]
}
