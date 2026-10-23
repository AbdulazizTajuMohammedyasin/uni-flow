import { AtSign, CircleAlert, Info, Newspaper, type LucideIcon } from 'lucide-react'
import { Link } from 'react-router'

import { EmptyState } from '@/components/EmptyState'
import { ErrorState } from '@/components/ErrorState'
import { ItemList, ItemRow } from '@/components/ItemRow'
import { ListSkeleton } from '@/components/ListSkeleton'
import { PageHeader } from '@/components/PageHeader'
import { TodayBox } from '@/components/TodayBox'
import { useFeed } from '@/hooks/useFeed'
import { TIERS } from '@/lib/feed'
import { todayInMalaysia } from '@/lib/timetable'
import type { FeedItem, Tier } from '@/types/feed'

const TIER_ICONS: Record<Tier, LucideIcon> = {
  direct: AtSign,
  action: CircleAlert,
  important: Info,
  digest: Newspaper,
}

/**
 * / — "For you": what matters to me, most urgent first.
 * - "Needs you" groups the two urgent levels (named in it, action required) in amber.
 * - Important updates follow as a normal list; digest items ("good to know") come last, shorter.
 * - On wide screens the Today rail sits on the right and stays in view.
 * Every level keeps its own heading and region, and empty levels are hidden.
 */
export function ForYouPage() {
  const feed = useFeed()

  return (
    <div className="space-y-6 md:space-y-8">
      <PageHeader
        title="For you"
        description={`${todayInMalaysia()} · Only the information that matters to you, from your academic groups.`}
      />

      <div className="grid gap-6 md:gap-8 xl:grid-cols-[minmax(0,1fr)_20rem] xl:items-start">
        <TodayBox className="xl:sticky xl:top-10 xl:col-start-2 xl:row-start-1" />

        <div className="min-w-0 space-y-8 xl:col-start-1 xl:row-start-1">
          {feed.isPending ? (
            <ListSkeleton />
          ) : feed.isError ? (
            <ErrorState title="Could not load your feed" message="Check your connection and reload the page." />
          ) : feed.data.length === 0 ? (
            <EmptyState
              title="Nothing for you yet"
              description="Add your academic groups on the Groups page, and UniFlow will show what matters to you here."
              action={
                <Link to="/sources" className="text-sm font-medium text-foreground underline underline-offset-4 hover:decoration-2">
                  Go to Groups
                </Link>
              }
            />
          ) : (
            <Feed items={feed.data} />
          )}
        </div>
      </div>
    </div>
  )
}

function Feed({ items }: { items: FeedItem[] }) {
  const of = (tier: Tier) => items.filter((item) => item.tier === tier)
  const urgent = of('direct').length + of('action').length

  return (
    <>
      {urgent > 0 && (
        <div className="space-y-4">
          <h2 className="text-lg font-medium">
            Needs you <span className="font-normal text-muted-foreground tabular-nums">({urgent})</span>
          </h2>
          <TierSection tier="direct" items={of('direct')} />
          <TierSection tier="action" items={of('action')} />
        </div>
      )}
      <TierSection tier="important" items={of('important')} />
      <TierSection tier="digest" items={of('digest')} />
    </>
  )
}

/** One level: its heading (icon + name + hint) and its items. Nothing when it is empty. */
function TierSection({ tier, items }: { tier: Tier; items: FeedItem[] }) {
  if (items.length === 0) return null
  const { title, hint } = TIERS.find((level) => level.tier === tier)!
  const Icon = TIER_ICONS[tier]
  const urgent = tier === 'direct' || tier === 'action'
  // Urgent levels sit under the "Needs you" heading (h2), so theirs is one level down.
  const Heading = urgent ? 'h3' : 'h2'

  return (
    <section aria-label={title} className="space-y-2">
      <div className="flex flex-wrap items-end justify-between gap-x-3">
        <div>
          <Heading className={urgent ? 'flex items-center gap-2 text-sm font-medium' : 'flex items-center gap-2 text-lg font-medium'}>
            <Icon aria-hidden className={urgent ? 'size-4 text-attention-foreground' : 'size-[1.125rem] text-muted-foreground'} />
            {title}
          </Heading>
          <p className="text-xs text-muted-foreground">{hint}</p>
        </div>
        {tier === 'digest' && (
          <Link to="/digest" className="text-sm font-medium text-foreground underline underline-offset-4 hover:decoration-2">
            Open the daily digest
          </Link>
        )}
      </div>
      <ItemList tone={urgent ? 'attention' : 'default'}>
        {items.map((item) => (
          <ItemRow key={item.id} item={item} compact={tier === 'digest'} />
        ))}
      </ItemList>
    </section>
  )
}
