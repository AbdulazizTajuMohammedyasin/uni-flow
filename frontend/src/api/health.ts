import type { Health } from '@/types/health'

import { api } from './client'
import { toApiError } from './errors'

/** GET /api/v1/health/: is the API up, and can it reach the database? */
export async function getHealth(): Promise<Health> {
  try {
    const response = await api.get<Health>('/health/')
    return response.data
  } catch (error) {
    throw toApiError(error)
  }
}
