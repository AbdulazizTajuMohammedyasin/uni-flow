/** Shown while a page's code is still downloading (lazy-loaded routes). */
export function PageLoading() {
  return (
    <div role="status" className="flex min-h-screen items-center justify-center text-muted-foreground">
      Loading…
    </div>
  )
}
