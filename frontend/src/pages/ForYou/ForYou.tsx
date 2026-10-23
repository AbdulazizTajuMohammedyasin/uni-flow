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
import { cn } from '@/lib/utils'
import type { FeedItem, Tier } from '@/types/feed'

const TIER_ICONS: Record<Tier, LucideIcon> = {
  direct: AtSign,
  action: CircleAlert,
  important: Info,
  digest: Newspaper,
}

/**
 * / — "For you": what matters to me, most urgent first.
 * - "Needs you" groups the two urgent levels (named in it, action required) in the dark block.
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
        <div className="space-y-1 overflow-hidden island rounded-[1.25rem] pt-4 pb-1 md:pt-5">
          <h2 className="px-5 text-xl leading-tight font-medium tracking-[-0.02em] md:text-[1.375rem]">
            Needs you <span className="font-normal text-island-muted tabular-nums">({urgent})</span>
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
    <section aria-label={title} className={urgent ? 'pt-3 [&+&]:mt-1 [&+&]:border-t [&+&]:border-island-muted/25 [&+&]:pt-4' : 'space-y-3'}>
      <div className={cn('flex flex-wrap items-end justify-between gap-x-3', urgent && 'px-5')}>
        <div>
          <Heading
            className={
              urgent
                ? 'flex items-center gap-2 text-sm font-medium text-primary'
                : 'flex items-center gap-2 text-[1.375rem] leading-tight font-medium tracking-[-0.02em]'
            }
          >
            <Icon aria-hidden className={urgent ? 'size-4' : 'size-5 text-muted-foreground'} />
            {title}
          </Heading>
          <p className={cn('text-[0.8125rem]', urgent ? 'text-island-muted' : 'text-muted-foreground')}>{hint}</p>
        </div>
        {tier === 'digest' && (
          <Link to="/digest" className="text-sm font-medium text-foreground underline underline-offset-4 hover:decoration-2">
            Open the daily digest
          </Link>
        )}
      </div>
      <ItemList tone={urgent ? 'island' : 'default'}>
        {items.map((item) => (
          <ItemRow key={item.id} item={item} compact={tier === 'digest'} tone={urgent ? 'island' : 'default'} />
        ))}
      </ItemList>
    </section>
  )
}
