import type { ReactNode } from 'react'
import { Link } from 'react-router'

import { Badge } from '@/components/ui/badge'
import { formatWhen } from '@/lib/feed'
import { cn } from '@/lib/utils'
import type { FeedItem } from '@/types/feed'

/** "default": a white panel. "island": rows inside the dark "needs you" block (no panel of their own). */
type Tone = 'default' | 'island'

/** Rows of items in one list, separated by lines (not a stack of separate cards). */
export function ItemList({ children, tone = 'default' }: { children: ReactNode; tone?: Tone }) {
  return (
    <ul
      className={cn(
        'divide-y overflow-hidden',
        tone === 'island' ? 'divide-island-muted/25' : 'divide-border rounded-2xl bg-card dark:ring-1 dark:ring-border',
      )}
    >
      {children}
    </ul>
  )
}

/** "Due Tue 20 Oct, 16:00 · You are in CCS2223 Section C2": when it is, and why I see it. */
function byline(item: FeedItem): string {
  const when = item.deadline_at ? `Due ${formatWhen(item.deadline_at)}` : item.starts_at ? formatWhen(item.starts_at) : ''
  return [when, item.reason].filter(Boolean).join(' · ')
}

/** One item that opens its page (For you, search results). "compact" leaves out the summary. */
export function ItemRow({ item, compact = false, tone = 'default' }: { item: FeedItem; compact?: boolean; tone?: Tone }) {
  const island = tone === 'island'
  const quiet = island ? 'text-island-muted' : 'text-muted-foreground'
  return (
    <li>
      <Link
        to={`/insights/${item.id}`}
        className={cn(
          'flex gap-3.5 px-5 py-4 outline-none focus-visible:ring-3 focus-visible:ring-inset',
          island
            ? 'hover:bg-island-foreground/5 focus-visible:ring-primary'
            : 'hover:bg-muted/60 focus-visible:bg-muted/60 focus-visible:ring-ring/50',
        )}
      >
        {/* Unread: a lime dot plus a heavier title; the dot is named for screen readers. On white it
            gets an ink ring, because lime alone is faint there. */}
        <span className="flex w-2 shrink-0 justify-center pt-2">
          {!item.read && (
            <span
              aria-label="Unread"
              className={cn('size-2 rounded-full bg-primary', !island && 'ring-[1.5px] ring-foreground dark:ring-0')}
            />
          )}
        </span>
        <span className="min-w-0 flex-1 space-y-1">
          <span className="flex flex-wrap items-center gap-x-2 gap-y-1">
            <span
              className={cn(
                'text-base leading-snug',
                island ? 'text-island-foreground' : 'text-foreground',
                item.read ? 'font-normal' : 'font-medium',
              )}
            >
              {item.title}
            </span>
            {item.official && (
              <Badge variant="secondary" className={island ? 'bg-island-foreground/10 text-island-foreground' : undefined}>
                Official
              </Badge>
            )}
            {item.not_confirmed && (
              <Badge variant="outline" className={island ? 'border-island-muted text-island-foreground' : undefined}>
                Not confirmed
              </Badge>
            )}
          </span>
          {!compact && item.summary && <span className={cn('line-clamp-2 block text-[0.9375rem]', quiet)}>{item.summary}</span>}
          <span className={cn('block text-[0.8125rem]', quiet)}>{byline(item)}</span>
        </span>
      </Link>
    </li>
  )
}
