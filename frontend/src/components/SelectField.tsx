import { useId, type ComponentProps, type ReactNode } from 'react'

import { Label } from '@/components/ui/label'
import { cn } from '@/lib/utils'

type SelectFieldProps = ComponentProps<'select'> & {
  label: string
  error?: string
  children: ReactNode
}

/** A labelled dropdown (the browser's own <select>, styled like the inputs). */
export function SelectField({ label, error, className, children, ...selectProps }: SelectFieldProps) {
  const id = useId()
  const errorId = `${id}-error`
  return (
    <div className="space-y-1.5">
      <Label htmlFor={id}>{label}</Label>
      <select
        id={id}
        aria-invalid={error ? true : undefined}
        aria-describedby={error ? errorId : undefined}
        className={cn(
          'h-11 w-full rounded-lg border border-input bg-card px-3 text-base shadow-xs outline-none md:h-9 md:text-sm',
          'focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50',
          'disabled:cursor-not-allowed disabled:opacity-50 aria-invalid:border-destructive',
          className,
        )}
        {...selectProps}
      >
        {children}
      </select>
      {error && (
        <p id={errorId} className="text-sm text-destructive">
          {error}
        </p>
      )}
    </div>
  )
}
