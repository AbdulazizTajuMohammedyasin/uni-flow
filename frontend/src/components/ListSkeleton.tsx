import { Skeleton } from '@/components/ui/skeleton'

/** Grey placeholder rows shown while a list loads: the page keeps its shape instead of
 * jumping. Screen readers hear "Loading…" once. */
export function ListSkeleton({ rows = 3 }: { rows?: number }) {
  return (
    <div role="status" aria-busy="true" className="divide-y divide-border overflow-hidden rounded-2xl bg-card dark:ring-1 dark:ring-border">
      <span className="sr-only">Loading…</span>
      {Array.from({ length: rows }, (_, index) => (
        <div key={index} aria-hidden className="space-y-2 px-4 py-4">
          <Skeleton className="h-4 w-2/3 motion-reduce:animate-none" />
          <Skeleton className="h-3.5 w-full motion-reduce:animate-none" />
          <Skeleton className="h-3 w-1/3 motion-reduce:animate-none" />
        </div>
      ))}
    </div>
  )
}
