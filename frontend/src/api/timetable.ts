import type { AddSectionData, Page, Section, TimetableDays } from '@/types/timetable'

import { api } from './client'
import { toApiError } from './errors'

/** Sections of the current term, optionally searched by course code or name. */
export async function getSections(search: string): Promise<Page<Section>> {
  try {
    const params = search ? { search } : undefined
    return (await api.get<Page<Section>>('/timetable/sections/', { params })).data
  } catch (error) {
    throw toApiError(error)
  }
}

export async function getMySections(): Promise<Section[]> {
  try {
    return (await api.get<Section[]>('/timetable/my-sections/')).data
  } catch (error) {
    throw toApiError(error)
  }
}

export async function joinSection(sectionId: number): Promise<Section> {
  try {
    return (await api.post<Section>('/timetable/my-sections/', { section: sectionId })).data
  } catch (error) {
    throw toApiError(error)
  }
}

export async function leaveSection(sectionId: number): Promise<void> {
  try {
    await api.delete(`/timetable/my-sections/${sectionId}/`)
  } catch (error) {
    throw toApiError(error)
  }
}

/** Add a class that is not in UniFlow yet (or join it if a classmate already added it). */
export async function addSectionByHand(data: AddSectionData): Promise<Section> {
  try {
    return (await api.post<Section>('/timetable/sections/', data)).data
  } catch (error) {
    throw toApiError(error)
  }
}

export async function getToday(): Promise<TimetableDays> {
  try {
    return (await api.get<TimetableDays>('/timetable/today/')).data
  } catch (error) {
    throw toApiError(error)
  }
}

/** Monday to Sunday of the week containing `date` (YYYY-MM-DD), or this week. */
export async function getWeek(date?: string): Promise<TimetableDays> {
  try {
    const params = date ? { date } : undefined
    return (await api.get<TimetableDays>('/timetable/week/', { params })).data
  } catch (error) {
    throw toApiError(error)
  }
}
