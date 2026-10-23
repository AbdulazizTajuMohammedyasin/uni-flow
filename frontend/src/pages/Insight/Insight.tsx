import { CalendarDays, CircleAlert, Clock, ExternalLink, MapPin, MessageSquareQuote, type LucideIcon } from 'lucide-react'
import { useEffect } from 'react'
import { Link, useNavigate, useParams } from 'react-router'

import { ApiError } from '@/api/errors'
import { BackLink } from '@/components/BackLink'
import { ErrorState } from '@/components/ErrorState'
import { ListSkeleton } from '@/components/ListSkeleton'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { useFeedItem, useUpdateFeedItem } from '@/hooks/useFeed'
import { formatWhen, kindLabel } from '@/lib/feed'
import type { Evidence, FeedDetail } from '@/types/feed'

/** /insights/:insightId — one item: what it is, why I see it, what to do, and the original messages. */
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

  if (item.isPending) {
    return (
      <div className="max-w-3xl space-y-6">
        <BackLink />
        <ListSkeleton rows={2} />
      </div>
    )
  }
  if (item.isError) {
    const missing = item.error instanceof ApiError && item.error.status === 404
    return (
      <div className="max-w-3xl space-y-6">
        <BackLink />
        <ErrorState title={missing ? 'This item is not in your feed' : 'Could not load this item'} />
      </div>
    )
  }

  const hide = (action: 'dismiss' | 'not_relevant') =>
    update.mutate({ id, action }, { onSuccess: () => navigate('/') })

  return (
    <article className="max-w-3xl space-y-8">
      <div className="space-y-4">
        <BackLink />
        <Header item={item.data} />
      </div>
      <Details item={item.data} />

      <section aria-label="Where it came from" className="space-y-3">
        <h2 className="flex items-center gap-2 text-lg font-medium">
          <MessageSquareQuote aria-hidden className="size-[1.125rem] text-muted-foreground" />
          Where it came from
        </h2>
        {item.data.evidence.length === 0 ? (
          <p className="text-sm text-muted-foreground">Posted directly in UniFlow by staff.</p>
        ) : (
          <ul className="divide-y divide-border overflow-hidden rounded-2xl bg-card dark:ring-1 dark:ring-border">
            {item.data.evidence.map((evidence) => (
              <EvidenceRow key={`${evidence.group.id}-${evidence.sent_at}`} evidence={evidence} />
            ))}
          </ul>
        )}
      </section>

      <div className="flex flex-wrap items-center gap-2 border-t border-border pt-6">
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
    <header className="space-y-3">
      <div className="flex flex-wrap gap-2">
        <Badge variant="secondary">{kindLabel(item.kind)}</Badge>
        {item.official && <Badge>Official</Badge>}
        {item.not_confirmed && <Badge variant="outline">Not confirmed</Badge>}
      </div>
      <h1 className="text-[1.625rem] leading-tight font-medium tracking-[-0.025em] text-balance md:text-[2.5rem] md:leading-[1.05] md:tracking-[-0.03em]">
        {item.title}
      </h1>
      <p className="max-w-[65ch] text-base md:text-lg">{item.summary}</p>
      <p className="w-fit max-w-[65ch] rounded-xl bg-muted px-3.5 py-2.5 text-sm text-foreground">
        Why you see this: {item.reason}
      </p>
    </header>
  )
}

function Details({ item }: { item: FeedDetail }) {
  const rows = [
    item.starts_at && { label: 'When', value: formatWhen(item.starts_at), Icon: CalendarDays },
    item.deadline_at && { label: 'Deadline', value: formatWhen(item.deadline_at), Icon: Clock },
    item.location && { label: 'Where', value: item.location, Icon: MapPin },
  ].filter(Boolean) as { label: string; value: string; Icon: LucideIcon }[]
  const change = item.timetable_change
  if (!item.action_required && rows.length === 0 && !item.link && !change) return null

  return (
    <div className="space-y-4">
      {item.action_required && (
        <p role="note" className="flex gap-2.5 island rounded-2xl p-4 text-[0.9375rem] md:p-5">
          <CircleAlert aria-hidden className="mt-0.5 size-4 shrink-0 text-primary" />
          <span>
            <span className="font-medium">What to do:</span> {item.action_text || 'Action needed.'}
          </span>
        </p>
      )}
      {rows.length > 0 && (
        <dl className="grid gap-x-6 gap-y-3 rounded-2xl bg-card p-4 sm:grid-cols-2 md:p-5 dark:ring-1 dark:ring-border">
          {rows.map(({ label, value, Icon }) => (
            <div key={label} className="flex gap-3">
              <Icon aria-hidden className="mt-0.5 size-4 shrink-0 text-muted-foreground" />
              <div>
                <dt className="text-xs text-muted-foreground">{label}</dt>
                <dd className="text-sm font-medium">{value}</dd>
              </div>
            </div>
          ))}
        </dl>
      )}
      {item.link && (
        <Button asChild variant="outline">
          <a href={item.link} target="_blank" rel="noreferrer">
            Open the link
            <ExternalLink aria-hidden />
          </a>
        </Button>
      )}
      {change && change.my_status === 'pending' && (
        <p className="island rounded-2xl p-4 text-[0.9375rem] md:p-5">
          This changes one of your classes.{' '}
          <Link
            to="/timetable"
            className="rounded-sm font-medium text-primary underline underline-offset-4 outline-none hover:decoration-2 focus-visible:ring-3 focus-visible:ring-primary"
          >
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

function EvidenceRow({ evidence }: { evidence: Evidence }) {
  return (
    <li className="space-y-2 p-4">
      <blockquote className="border-l-2 border-border pl-3 text-[0.9375rem]">“{evidence.quote}”</blockquote>
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="text-xs text-muted-foreground">
          <span className="font-medium text-foreground">{evidence.sender_name || 'Someone'}</span> in{' '}
          {evidence.group.title} · {formatWhen(evidence.sent_at)}
        </p>
        {evidence.open_url && (
          <Button asChild size="sm" variant="outline">
            <a href={evidence.open_url} target="_blank" rel="noreferrer">
              Open original
              <ExternalLink aria-hidden />
            </a>
          </Button>
        )}
      </div>
    </li>
  )
}
