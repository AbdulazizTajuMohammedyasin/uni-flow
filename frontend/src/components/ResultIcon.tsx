import type { LucideIcon } from 'lucide-react'

import { cn } from '@/lib/utils'

/** The round icon above a finished step ("Check your email", "Password changed"). */
export function ResultIcon({ icon: Icon, tone = 'primary' }: { icon: LucideIcon; tone?: 'primary' | 'success' | 'destructive' }) {
  return (
    <span
      className={cn(
        'mx-auto mb-4 flex size-12 items-center justify-center rounded-full',
        tone === 'primary' && 'bg-primary/10 text-primary',
        tone === 'success' && 'bg-success/10 text-success',
        tone === 'destructive' && 'bg-destructive/10 text-destructive',
      )}
    >
      <Icon aria-hidden className="size-6" />
    </span>
  )
}
