import { QueryClientProvider } from '@tanstack/react-query'
import type { ReactNode } from 'react'

import { createQueryClient } from './queryClient'

const queryClient = createQueryClient()

/** App-wide providers. Authentication is added here in M1.9. */
export function Providers({ children }: { children: ReactNode }) {
  return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
}
