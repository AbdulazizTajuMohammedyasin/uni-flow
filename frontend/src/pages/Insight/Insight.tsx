import { useEffect } from 'react'
import { Link, useNavigate, useParams } from 'react-router'

import { ApiError } from '@/api/errors'
import { ErrorState } from '@/components/ErrorState'
import { PageLoading } from '@/components/PageLoading'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { useFeedItem, useUpdateFeedItem } from '@/hooks/useFeed'
import { formatWhen, kindLabel } from '@/lib/feed'
import type { Evidence, FeedDetail } from '@/types/feed'

/** /insights/:insightId — one item: details, why I see it, and the original messages. */
export function InsightPage() {
  const id = Number(useParams().insightId)
  const item = useFeedItem(id)
  const update = useUpdateFeedItem()
  const navigate = useNavigate()
  const { mutate } = update

  // Opening an item marks it as read (once).
  const unread = item.data && !item.data.read
  useEffect(() => {
    if (unread) mutate({ id, action: 'read' })
  }, [unread, id, mutate])

  if (item.isPending) return <PageLoading />
  if (item.isError) {
    const missing = item.error instanceof ApiError && item.error.status === 404
    return <ErrorState title={missing ? 'This item is not in your feed' : 'Could not load this item'} />
  }

  const hide = (action: 'dismiss' | 'not_relevant') =>
    update.mutate({ id, action }, { onSuccess: () => navigate('/') })

  return (
    <article className="max-w-3xl space-y-6">
      <Link to="/" className="text-sm text-muted-foreground hover:underline">
        ← For you
      </Link>
      <Header item={item.data} />
      <Details item={item.data} />

      <section aria-label="Where it came from" className="space-y-2">
        <h2 className="font-semibold">Where it came from</h2>
        {item.data.evidence.length === 0 ? (
          <p className="text-sm text-muted-foreground">Posted directly in UniFlow by staff.</p>
        ) : (
          <ul className="space-y-2">
            {item.data.evidence.map((evidence) => (
              <EvidenceCard key={`${evidence.group.id}-${evidence.sent_at}`} evidence={evidence} />
            ))}
          </ul>
        )}
      </section>

      <div className="flex flex-wrap gap-2">
        <Button variant="outline" disabled={update.isPending} onClick={() => hide('dismiss')}>
          Dismiss
        </Button>
        <Button variant="ghost" disabled={update.isPending} onClick={() => hide('not_relevant')}>
          Not relevant to me
        </Button>
      </div>
    </article>
  )
}

function Header({ item }: { item: FeedDetail }) {
  return (
    <header className="space-y-2">
      <div className="flex flex-wrap gap-2">
        <Badge variant="secondary">{kindLabel(item.kind)}</Badge>
        {item.official && <Badge>Official</Badge>}
        {item.not_confirmed && <Badge variant="outline">Not confirmed</Badge>}
      </div>
      <h1 className="text-2xl font-bold tracking-tight">{item.title}</h1>
      <p>{item.summary}</p>
      <p className="text-sm text-muted-foreground">Why you see this: {item.reason}</p>
    </header>
  )
}

function Details({ item }: { item: FeedDetail }) {
  const rows = [
    item.starts_at && ['When', formatWhen(item.starts_at)],
    item.deadline_at && ['Deadline', formatWhen(item.deadline_at)],
    item.location && ['Where', item.location],
  ].filter(Boolean) as [string, string][]
  const change = item.timetable_change

  return (
    <div className="space-y-3">
      {item.action_required && (
        <p role="note" className="rounded-xl bg-amber-50 p-3 text-sm ring-1 ring-amber-200">
          <span className="font-semibold">What to do:</span> {item.action_text || 'Action needed.'}
        </p>
      )}
      {rows.length > 0 && (
        <dl className="grid grid-cols-[auto_1fr] gap-x-4 gap-y-1 text-sm">
          {rows.map(([label, value]) => (
            <div key={label} className="contents">
              <dt className="text-muted-foreground">{label}</dt>
              <dd>{value}</dd>
            </div>
          ))}
        </dl>
      )}
      {item.link && (
        <a href={item.link} target="_blank" rel="noreferrer" className="text-sm text-primary underline">
          Open the link
        </a>
      )}
      {change && change.my_status === 'pending' && (
        <p className="text-sm">
          This changes one of your classes.{' '}
          <Link to="/timetable" className="text-primary underline">
            Confirm or reject it on your timetable
          </Link>
          .
        </p>
      )}
      {change && change.my_status !== 'pending' && (
        <p className="text-sm text-muted-foreground">You {change.my_status} this change on your timetable.</p>
      )}
    </div>
  )
}

function EvidenceCard({ evidence }: { evidence: Evidence }) {
  return (
    <li className="space-y-1 rounded-xl bg-card p-3 shadow-sm ring-1 ring-border">
      <blockquote className="border-l-2 border-border pl-3 text-sm">“{evidence.quote}”</blockquote>
      <p className="text-xs text-muted-foreground">
        {evidence.sender_name || 'Someone'} in {evidence.group.title} · {formatWhen(evidence.sent_at)}
      </p>
      {evidence.open_url && (
        <a href={evidence.open_url} target="_blank" rel="noreferrer" className="text-xs text-primary underline">
          Open original
        </a>
      )}
    </li>
  )
}
