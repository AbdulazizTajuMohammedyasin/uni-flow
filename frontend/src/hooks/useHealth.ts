import { useQuery } from '@tanstack/react-query'

import { getHealth } from '@/api/health'

/** Is the backend up (and can it reach the database)? Used by the dev-only HealthBadge. */
export function useHealth() {
  return useQuery({ queryKey: ['health'], queryFn: getHealth, retry: false })
}
