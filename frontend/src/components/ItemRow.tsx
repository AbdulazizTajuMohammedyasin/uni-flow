import type { ReactNode } from 'react'
import { Link } from 'react-router'

import { Badge } from '@/components/ui/badge'
import { formatWhen } from '@/lib/feed'
import { cn } from '@/lib/utils'
import type { FeedItem } from '@/types/feed'

/** Rows of items in one bordered list, separated by lines (not a stack of separate cards).
 * "attention" adds the amber edge used only for things that need the student. */
export function ItemList({ children, tone = 'default' }: { children: ReactNode; tone?: 'default' | 'attention' }) {
  return (
    <ul
      className={cn(
        'divide-y divide-border overflow-hidden rounded-xl bg-card ring-1 ring-border',
        tone === 'attention' && 'border-l-4 border-l-attention-border',
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
export function ItemRow({ item, compact = false }: { item: FeedItem; compact?: boolean }) {
  return (
    <li>
      <Link
        to={`/insights/${item.id}`}
        className="flex gap-3 px-4 py-3.5 outline-none hover:bg-muted/60 focus-visible:bg-muted/60 focus-visible:ring-3 focus-visible:ring-ring/50 focus-visible:ring-inset"
      >
        {/* Unread: a dot plus bold title; the dot is named for screen readers. */}
        <span className="flex w-2 shrink-0 justify-center pt-2">
          {!item.read && <span aria-label="Unread" className="size-2 rounded-full bg-primary" />}
        </span>
        <span className="min-w-0 flex-1 space-y-1">
          <span className="flex flex-wrap items-center gap-x-2 gap-y-1">
            <span className={cn('text-[0.9375rem] leading-snug text-foreground', item.read ? 'font-normal' : 'font-medium')}>
              {item.title}
            </span>
            {item.official && <Badge variant="secondary">Official</Badge>}
            {item.not_confirmed && <Badge variant="outline">Not confirmed</Badge>}
          </span>
          {!compact && item.summary && (
            <span className="line-clamp-2 block text-sm text-muted-foreground">{item.summary}</span>
          )}
          <span className="block text-xs text-muted-foreground">{byline(item)}</span>
        </span>
      </Link>
    </li>
  )
}
