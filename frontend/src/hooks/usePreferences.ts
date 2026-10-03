import { useQuery } from '@tanstack/react-query'

import { getPreferenceChoices } from '@/api/auth'

/** The interest and information-type options (they rarely change). */
export function usePreferenceChoices() {
  return useQuery({
    queryKey: ['preference-choices'],
    queryFn: getPreferenceChoices,
    staleTime: 60 * 60 * 1000,
  })
}
