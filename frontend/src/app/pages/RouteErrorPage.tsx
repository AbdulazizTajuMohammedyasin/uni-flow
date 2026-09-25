import { isRouteErrorResponse, useRouteError } from 'react-router'

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
            <button
              type="button"
              onClick={() => window.location.reload()}
              className="rounded-lg bg-red-600 px-4 py-2 font-medium text-white hover:bg-red-700"
            >
              Reload page
            </button>
          }
        />
      </div>
    </main>
  )
}
