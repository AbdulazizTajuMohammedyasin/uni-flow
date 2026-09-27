import { QueryClient } from '@tanstack/react-query'

import { ApiError } from '@/api/errors'

/** Retry a failed request once, but never retry 4xx errors (they will not fix themselves). */
function shouldRetry(failureCount: number, error: unknown): boolean {
  if (error instanceof ApiError && error.status !== null && error.status >= 400 && error.status < 500) {
    return false
  }
  return failureCount < 1
}

/** TanStack Query client with UniFlow's defaults (docs/05-frontend.md). */
export function createQueryClient(): QueryClient {
  return new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 30_000, // data counts as fresh for 30 s
        retry: shouldRetry,
        refetchOnWindowFocus: false,
      },
    },
  })
}
