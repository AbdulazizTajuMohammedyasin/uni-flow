import type { ReactNode } from 'react'

type ErrorStateProps = {
  title: string
  message?: string
  action?: ReactNode
}

/** Box shown when something failed. `role="alert"` makes screen readers announce it. */
export function ErrorState({ title, message, action }: ErrorStateProps) {
  return (
    <div role="alert" className="rounded-2xl border border-destructive/30 bg-destructive/10 px-6 py-10 text-center">
      <p className="font-medium text-destructive">{title}</p>
      {message && <p className="mt-1 text-sm text-foreground">{message}</p>}
      {action && <div className="mt-4">{action}</div>}
    </div>
  )
}
