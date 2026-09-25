import { EmptyState } from '@/shared/ui/EmptyState'

type PlaceholderPageProps = {
  title: string
  description?: string
}

/** Temporary page for sections that later milestones will build. */
export function PlaceholderPage({ title, description }: PlaceholderPageProps) {
  return (
    <section>
      <h1 className="text-2xl font-bold tracking-tight">{title}</h1>
      <div className="mt-6">
        <EmptyState
          title="Coming soon"
          description={description ?? 'This section is part of an upcoming milestone.'}
        />
      </div>
    </section>
  )
}
