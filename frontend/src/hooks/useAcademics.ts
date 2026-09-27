import { useQuery } from '@tanstack/react-query'

import { getIntakes, getProgrammes, getSchools } from '@/api/academics'

// These lists rarely change: keep them fresh for 10 minutes.
const TEN_MINUTES = 10 * 60 * 1000

export function useSchools() {
  return useQuery({ queryKey: ['schools'], queryFn: getSchools, staleTime: TEN_MINUTES })
}

/** Programmes of one school; nothing is loaded until a school is chosen. */
export function useProgrammes(schoolId: number | null) {
  return useQuery({
    queryKey: ['programmes', schoolId],
    queryFn: () => getProgrammes(schoolId ?? undefined),
    enabled: schoolId !== null,
    staleTime: TEN_MINUTES,
  })
}

export function useIntakes() {
  return useQuery({ queryKey: ['intakes'], queryFn: getIntakes, staleTime: TEN_MINUTES })
}
