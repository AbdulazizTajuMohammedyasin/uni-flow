import { isRouteErrorResponse, useRouteError } from 'react-router'

import { Button } from '@/components/ui/button'
import { ErrorState } from '@/shared/ui/ErrorState'

import { NotFoundPage } from './NotFoundPage'

/** Catches errors thrown while loading or rendering any page (the route `errorElement`). */
export function RouteErrorPage() {
  const error = useRouteError()

  if (isRouteErrorResponse(error) && error.status === 404) {
    return <NotFoundPage />
  }

  return (
    <main className="flex min-h-screen items-center justify-center px-4">
      <div className="w-full max-w-md">
        <ErrorState
          title="Something went wrong"
          message="An unexpected error occurred. Reloading the page usually helps."
          action={
            <Button type="button" size="lg" onClick={() => window.location.reload()}>
              Reload page
            </Button>
          }
        />
      </div>
    </main>
  )
}
