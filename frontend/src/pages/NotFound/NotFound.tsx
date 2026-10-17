import { Link } from 'react-router'

import { Button } from '@/components/ui/button'

/** Shown for any address that does not match a route. */
export function NotFoundPage() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center px-4 text-center">
      <p className="text-sm font-semibold text-primary">404</p>
      <h1 className="mt-2 text-3xl font-bold tracking-tight">Page not found</h1>
      <p className="mt-2 text-muted-foreground">The page you are looking for does not exist.</p>
      <Button asChild size="lg" className="mt-6">
        <Link to="/">Go to home</Link>
      </Button>
    </main>
  )
}
