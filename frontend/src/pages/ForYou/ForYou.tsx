import { Link } from 'react-router'

import { EmptyState } from '@/components/EmptyState'
import { ErrorState } from '@/components/ErrorState'
import { PageLoading } from '@/components/PageLoading'
import { Badge } from '@/components/ui/badge'
import { useFeed } from '@/hooks/useFeed'
import { formatWhen, TIERS } from '@/lib/feed'
import type { FeedItem } from '@/types/feed'

/** / — "For you": what matters to me, in four levels (empty levels are hidden). */
export function ForYouPage() {
  const feed = useFeed()

  return (
    <div className="max-w-3xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">For you</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Only the information that matters to you, from your academic groups.
        </p>
      </div>

      {feed.isPending ? (
        <PageLoading />
      ) : feed.isError ? (
        <ErrorState title="Could not load your feed" />
      ) : feed.data.length === 0 ? (
        <EmptyState
          title="Nothing for you yet"
          description="Add your academic groups on the Groups page, and UniFlow will show what matters to you here."
        />
      ) : (
        TIERS.map(({ tier, title, hint }) => {
          const items = feed.data.filter((item) => item.tier === tier)
          if (items.length === 0) return null
          return (
            <section key={tier} aria-label={title} className="space-y-2">
              <div>
                <h2 className="font-semibold">{title}</h2>
                <p className="text-xs text-muted-foreground">{hint}</p>
              </div>
              <ul className="space-y-2">
                {items.map((item) => (
                  <ItemCard key={item.id} item={item} />
                ))}
              </ul>
            </section>
          )
        })
      )}
    </div>
  )
}

function ItemCard({ item }: { item: FeedItem }) {
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
