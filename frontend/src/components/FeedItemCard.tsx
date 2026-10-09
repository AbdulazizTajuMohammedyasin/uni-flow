import { Link } from 'react-router'

import { Badge } from '@/components/ui/badge'
import { formatWhen } from '@/lib/feed'
import type { FeedItem } from '@/types/feed'

/** One item as a card that opens its item page (For you, search results). */
export function FeedItemCard({ item }: { item: FeedItem }) {
  const when = item.deadline_at
    ? `Due ${formatWhen(item.deadline_at)}`
    : item.starts_at
      ? formatWhen(item.starts_at)
      : ''
  return (
    <li>
      <Link
        to={`/insights/${item.id}`}
        className="block space-y-1 rounded-xl bg-card p-3 shadow-sm ring-1 ring-border hover:ring-primary/40"
      >
        <div className="flex flex-wrap items-center gap-2">
          {!item.read && <span aria-label="Unread" className="size-2 rounded-full bg-primary" />}
          <p className={item.read ? 'font-medium' : 'font-semibold'}>{item.title}</p>
          {item.official && <Badge variant="secondary">Official</Badge>}
          {item.not_confirmed && <Badge variant="outline">Not confirmed</Badge>}
        </div>
        <p className="text-sm text-muted-foreground">{item.summary}</p>
        <p className="text-xs text-muted-foreground">
          {[when, item.reason].filter(Boolean).join(' · ')}
        </p>
      </Link>
    </li>
  )
}
