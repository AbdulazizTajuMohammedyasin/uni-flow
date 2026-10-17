import { EmptyState } from '@/components/EmptyState'
import { PageHeader } from '@/components/PageHeader'

type PlaceholderPageProps = {
  title: string
  description?: string
}

/** Temporary page for sections that later milestones will build. */
export function PlaceholderPage({ title, description }: PlaceholderPageProps) {
  return (
    <section>
      <PageHeader title={title} />
      <div className="mt-6">
        <EmptyState
          title="Coming soon"
          description={description ?? 'This section is part of an upcoming milestone.'}
        />
      </div>
    </section>
  )
}
