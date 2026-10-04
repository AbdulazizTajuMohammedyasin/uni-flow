import type { ImportResult, Source } from '@/types/sources'

import { api } from './client'
import { toApiError } from './errors'

/** The groups I added. */
export async function getMySources(): Promise<Source[]> {
  try {
    return (await api.get<Source[]>('/sources/')).data
  } catch (error) {
    throw toApiError(error)
  }
}

/** A group for pasted or uploaded messages. */
export async function createSource(title: string): Promise<Source> {
  try {
    return (await api.post<Source>('/sources/', { title })).data
  } catch (error) {
    throw toApiError(error)
  }
}

/** Messages copied from WhatsApp (or one plain message). */
export async function pasteMessages(sourceId: number, text: string): Promise<ImportResult> {
  try {
    return (await api.post<ImportResult>(`/sources/${sourceId}/paste/`, { text })).data
  } catch (error) {
    throw toApiError(error)
  }
}

/** WhatsApp's "Export chat" .txt file. */
export async function uploadExport(sourceId: number, file: File): Promise<ImportResult> {
  const form = new FormData()
  form.append('file', file)
  try {
    return (await api.post<ImportResult>(`/sources/${sourceId}/export/`, form)).data
  } catch (error) {
    throw toApiError(error)
  }
}
