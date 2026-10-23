import { Link, useSearchParams } from 'react-router'

import { BackLink } from '@/components/BackLink'
import { EmptyState } from '@/components/EmptyState'
import { ErrorState } from '@/components/ErrorState'
import { ListSkeleton } from '@/components/ListSkeleton'
import { PageHeader } from '@/components/PageHeader'
import { Badge } from '@/components/ui/badge'
import { useDigest } from '@/hooks/useFeed'
import { formatDay } from '@/lib/timetable'
import { INFO_TYPE_LABELS } from '@/lib/feed'
import type { FeedItem } from '@/types/feed'

/** /digest?date=YYYY-MM-DD — one day's "good to know" items, grouped by type. The daily
 * digest alert opens this page; without a date it shows my latest digest. */
export function DigestPage() {
  const [params] = useSearchParams()
  const digest = useDigest(params.get('date') ?? undefined)

  if (digest.isPending) return <ListSkeleton />
  if (digest.isError) return <ErrorState title="Could not load your digest" />

  const { date, items } = digest.data
  const groups = Object.entries(INFO_TYPE_LABELS)
    .map(([type, label]) => ({ label, items: items.filter((item) => item.info_type === type) }))
    .filter((group) => group.items.length > 0)

  return (
    <div className="max-w-3xl space-y-6">
      <div className="space-y-2">
        <BackLink />
        <PageHeader
          title="Daily digest"
          description={date ? `Good to know, ${formatDay(date)}.` : 'Your first digest arrives one evening at 7 pm.'}
        />
      </div>

      {items.length === 0 ? (
        <EmptyState
          title="Nothing in this digest"
          description="Your digest collects the 'good to know' items of the day, once every evening."
        />
      ) : (
        groups.map((group) => (
          <section key={group.label} aria-label={group.label} className="space-y-2">
            <h2 className="text-lg font-medium">
              {group.label} <span className="font-normal text-muted-foreground tabular-nums">({group.items.length})</span>
            </h2>
            <ul className="divide-y divide-border overflow-hidden rounded-xl bg-card ring-1 ring-border">
              {group.items.map((item) => (
                <DigestRow key={item.id} item={item} />
              ))}
            </ul>
          </section>
        ))
      )}
    </div>
  )
}

function DigestRow({ item }: { item: FeedItem }) {
  return (
    <li>
      <Link
        to={`/insights/${item.id}`}
        className="block space-y-1 px-4 py-3.5 outline-none hover:bg-muted/60 focus-visible:bg-muted/60 focus-visible:ring-3 focus-visible:ring-ring/50 focus-visible:ring-inset"
      >
        <div className="flex flex-wrap items-center gap-2">
          <p className="text-[0.9375rem] leading-snug font-medium">{item.title}</p>
          {item.not_confirmed && <Badge variant="outline">Not confirmed</Badge>}
        </div>
        <p className="line-clamp-2 text-sm text-muted-foreground">{item.summary}</p>
      </Link>
    </li>
  )
}
