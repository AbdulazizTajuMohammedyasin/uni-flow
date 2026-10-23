import type { ReactNode } from 'react'

type PageHeaderProps = {
  title: string
  description?: ReactNode
  /** Buttons or toggles shown on the right (below the title on narrow phones). */
  actions?: ReactNode
}

/** The title row every page starts with: one size and spacing everywhere. */
export function PageHeader({ title, description, actions }: PageHeaderProps) {
  return (
    <header className="flex flex-wrap items-end justify-between gap-x-4 gap-y-3">
      <div className="min-w-0 space-y-1.5 md:space-y-2">
        <h1 className="text-[1.625rem] leading-tight font-medium tracking-[-0.025em] text-balance md:text-[2.5rem] md:leading-[1.05] md:tracking-[-0.03em]">
          {title}
        </h1>
        {description && <p className="max-w-[65ch] text-sm text-muted-foreground md:text-base">{description}</p>}
      </div>
      {actions && <div className="flex shrink-0 flex-wrap items-center gap-2">{actions}</div>}
    </header>
  )
}
