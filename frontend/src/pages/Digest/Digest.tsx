import { Link, useSearchParams } from 'react-router'

import { EmptyState } from '@/components/EmptyState'
import { ErrorState } from '@/components/ErrorState'
import { PageHeader } from '@/components/PageHeader'
import { PageLoading } from '@/components/PageLoading'
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

  if (digest.isPending) return <PageLoading />
  if (digest.isError) return <ErrorState title="Could not load your digest" />

  const { date, items } = digest.data
  const groups = Object.entries(INFO_TYPE_LABELS)
    .map(([type, label]) => ({ label, items: items.filter((item) => item.info_type === type) }))
    .filter((group) => group.items.length > 0)

  return (
    <div className="max-w-3xl space-y-6">
      <div className="space-y-3">
        <Link to="/" className="text-sm text-muted-foreground hover:underline">
          ← For you
        </Link>
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
            <h2 className="font-semibold">{group.label}</h2>
            <ul className="space-y-2">
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
        className="block rounded-xl bg-card p-3 shadow-sm ring-1 ring-border hover:ring-primary/40"
      >
        <div className="flex flex-wrap items-center gap-2">
          <p className="font-medium">{item.title}</p>
          {item.not_confirmed && <Badge variant="outline">Not confirmed</Badge>}
        </div>
        <p className="text-sm text-muted-foreground">{item.summary}</p>
      </Link>
    </li>
  )
}
