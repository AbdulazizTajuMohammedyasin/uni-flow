import type { LucideIcon } from 'lucide-react'
import type { ReactNode } from 'react'

import { ResultIcon } from '@/components/ResultIcon'

type StatusMessageProps = {
  icon: LucideIcon
  tone?: 'primary' | 'destructive'
  /** A small line above the title, e.g. "404". */
  code?: string
  title: string
  children: ReactNode
  action: ReactNode
}

/** The centred message of the 404, 403 and "something went wrong" pages. */
export function StatusMessage({ icon, tone = 'primary', code, title, children, action }: StatusMessageProps) {
  return (
    <div className="mx-auto flex max-w-md flex-col items-center text-center">
      <ResultIcon icon={icon} tone={tone} />
      {code && <p className="text-sm font-medium text-muted-foreground">{code}</p>}
      <h1 className="mt-1 text-2xl font-medium tracking-tight md:text-[1.75rem]">{title}</h1>
      <p className="mt-2 text-muted-foreground">{children}</p>
      <div className="mt-6">{action}</div>
    </div>
  )
}
