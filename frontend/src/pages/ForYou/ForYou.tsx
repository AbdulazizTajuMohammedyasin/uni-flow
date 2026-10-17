import { EmptyState } from '@/components/EmptyState'
import { ErrorState } from '@/components/ErrorState'
import { FeedItemCard } from '@/components/FeedItemCard'
import { PageHeader } from '@/components/PageHeader'
import { PageLoading } from '@/components/PageLoading'
import { TodayBox } from '@/components/TodayBox'
import { useFeed } from '@/hooks/useFeed'
import { TIERS } from '@/lib/feed'

/** / — "For you": what matters to me, in four levels (empty levels are hidden). */
export function ForYouPage() {
  const feed = useFeed()

  return (
    <div className="max-w-3xl space-y-6">
      <PageHeader
        title="For you"
        description="Only the information that matters to you, from your academic groups."
      />

      <TodayBox />

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
                  <FeedItemCard key={item.id} item={item} />
                ))}
              </ul>
            </section>
          )
        })
      )}
    </div>
  )
}
