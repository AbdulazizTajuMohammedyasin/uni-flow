import type { ImportResult, Source, UnclaimedGroup } from '@/types/sources'

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

/** A WhatsApp group by its invite link: UniFlow's number joins it ("pending" until then).
 * If UniFlow already knows the group, I'm added to it instead. Without a link (""), I add
 * UniFlow's number to the group myself; the reply has added_by_number and the number. */
export async function connectSource(inviteUrl: string, title: string): Promise<Source> {
  try {
    return (await api.post<Source>('/sources/connect/', { invite_url: inviteUrl, title })).data
  } catch (error) {
    throw toApiError(error)
  }
}

/** For my group waiting for UniFlow's number: groups UniFlow joined since that nobody claimed. */
export async function getUnclaimedGroups(sourceId: number): Promise<UnclaimedGroup[]> {
  try {
    return (await api.get<UnclaimedGroup[]>(`/sources/${sourceId}/unclaimed/`)).data
  } catch (error) {
    throw toApiError(error)
  }
}

/** "This joined group is the one I added": my waiting entry becomes that group. */
export async function claimGroup(sourceId: number, groupId: number): Promise<Source> {
  try {
    return (await api.post<Source>(`/sources/${sourceId}/claim/`, { group: groupId })).data
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
