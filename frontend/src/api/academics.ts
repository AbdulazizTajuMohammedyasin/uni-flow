import type { Intake, Programme, School } from '@/types/academics'

import { api } from './client'
import { toApiError } from './errors'

export async function getSchools(): Promise<School[]> {
  try {
    return (await api.get<School[]>('/academics/schools/')).data
  } catch (error) {
    throw toApiError(error)
  }
}

/** All active programmes, or only one school's (`schoolId`). */
export async function getProgrammes(schoolId?: number): Promise<Programme[]> {
  try {
    const params = schoolId ? { school: schoolId } : undefined
    return (await api.get<Programme[]>('/academics/programmes/', { params })).data
  } catch (error) {
    throw toApiError(error)
  }
}

export async function getIntakes(): Promise<Intake[]> {
  try {
    return (await api.get<Intake[]>('/academics/intakes/')).data
  } catch (error) {
    throw toApiError(error)
  }
}
