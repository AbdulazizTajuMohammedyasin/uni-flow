import { TriangleAlert } from 'lucide-react'
import { isRouteErrorResponse, useRouteError } from 'react-router'

import { StatusMessage } from '@/components/StatusMessage'
import { Button } from '@/components/ui/button'

import { NotFoundPage } from '../NotFound/NotFound'

/** Catches errors thrown while loading or rendering any page (the route `errorElement`). */
export function RouteErrorPage() {
  const error = useRouteError()

  if (isRouteErrorResponse(error) && error.status === 404) {
    return <NotFoundPage />
  }

  return (
    <main className="flex min-h-screen items-center justify-center px-4 py-10">
      {/* Announced by screen readers, like the old error box. */}
      <div role="alert">
        <StatusMessage
          icon={TriangleAlert}
          tone="destructive"
          title="Something went wrong"
          action={
            <Button type="button" size="lg" onClick={() => window.location.reload()}>
              Reload page
            </Button>
          }
        >
          An unexpected error occurred. Reloading the page usually helps.
        </StatusMessage>
      </div>
    </main>
  )
}
