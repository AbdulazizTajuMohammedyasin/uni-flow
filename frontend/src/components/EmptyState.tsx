import type { ReactNode } from 'react'

type EmptyStateProps = {
  title: string
  description?: string
  action?: ReactNode
}

/** Friendly box shown when there is nothing to display yet. */
export function EmptyState({ title, description, action }: EmptyStateProps) {
  return (
    <div className="rounded-2xl border border-dashed border-border bg-card px-6 py-10 text-center">
      <p className="font-medium text-foreground">{title}</p>
      {description && <p className="mt-1 text-sm text-muted-foreground">{description}</p>}
      {action && <div className="mt-4">{action}</div>}
    </div>
  )
}
