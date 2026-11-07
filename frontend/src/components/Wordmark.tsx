import { cn } from '@/lib/utils'

/** The UniFlow name with its mark: a rounded blue square with two lines, like a short list. The mark is decorative. */
export function Wordmark({ className }: { className?: string }) {
  return (
    <span className={cn('inline-flex items-center gap-2 font-semibold tracking-tight', className)}>
      <span
        aria-hidden
        className="flex size-[1.1em] shrink-0 flex-col justify-center gap-[0.14em] rounded-[0.3em] bg-primary px-[0.24em]"
      >
        <span className="h-[0.11em] rounded-full bg-primary-foreground" />
        <span className="h-[0.11em] rounded-full bg-primary-foreground" />
      </span>
      UniFlow
    </span>
  )
}
