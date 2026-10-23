import { Monitor, Moon, Sun } from 'lucide-react'

import { useTheme } from '@/hooks/useTheme'
import type { Theme } from '@/lib/theme'
import { cn } from '@/lib/utils'

const OPTIONS: { value: Theme; label: string; Icon: typeof Sun }[] = [
  { value: 'light', label: 'Light', Icon: Sun },
  { value: 'dark', label: 'Dark', Icon: Moon },
  { value: 'system', label: 'System', Icon: Monitor },
]

/** Light / Dark / System, as one row of three choices (a radio group for screen readers). */
export function ThemeToggle({ className }: { className?: string }) {
  const [theme, chooseTheme] = useTheme()
  return (
    <div role="radiogroup" aria-label="Theme" className={cn('inline-flex gap-1 rounded-full bg-muted p-1', className)}>
      {OPTIONS.map(({ value, label, Icon }) => (
        <button
          key={value}
          type="button"
          role="radio"
          aria-checked={theme === value}
          onClick={() => chooseTheme(value)}
          className={cn(
            'inline-flex min-h-11 items-center gap-1.5 rounded-full border border-transparent px-3.5 text-sm font-medium transition-colors outline-none md:min-h-8',
            'focus-visible:ring-3 focus-visible:ring-ring/50',
            theme === value
              ? 'border-border bg-card text-foreground dark:border-transparent dark:bg-foreground dark:text-background'
              : 'text-muted-foreground hover:text-foreground',
          )}
        >
          <Icon aria-hidden className="size-4" />
          {label}
        </button>
      ))}
    </div>
  )
}
