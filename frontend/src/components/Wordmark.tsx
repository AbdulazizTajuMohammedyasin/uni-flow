import { cn } from '@/lib/utils'

/** The UniFlow name with its mark: a rounded square with two lines, like a short list.
 * `inverted` is for lime backgrounds (an ink square with lime lines, in both themes). The mark is decorative. */
export function Wordmark({ className, inverted = false }: { className?: string; inverted?: boolean }) {
  return (
    <span className={cn('inline-flex items-center gap-2 font-medium tracking-tight', className)}>
      <span
        aria-hidden
        className={cn(
          'flex size-[1.1em] shrink-0 flex-col justify-center gap-[0.14em] rounded-[0.3em] px-[0.24em]',
          inverted ? 'bg-primary-foreground' : 'bg-primary',
        )}
      >
        <span className={cn('h-[0.11em] rounded-full', inverted ? 'bg-primary' : 'bg-primary-foreground')} />
        <span className={cn('h-[0.11em] rounded-full', inverted ? 'bg-primary' : 'bg-primary-foreground')} />
      </span>
      UniFlow
    </span>
  )
}
