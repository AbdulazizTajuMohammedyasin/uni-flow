import type {
  AddSectionData,
  ClassChange,
  ImportRow,
  Page,
  Section,
  TimetableDays,
  TimetableImport,
} from '@/types/timetable'

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

/** "Add my timetable": a file (image, PDF, Excel) or a Google Drive link; reading starts. */
export async function startImport(input: { file: File } | { link: string }): Promise<TimetableImport> {
  try {
    if ('file' in input) {
      const form = new FormData()
      form.append('file', input.file)
      return (await api.post<TimetableImport>('/timetable/imports/', form)).data
    }
    return (await api.post<TimetableImport>('/timetable/imports/', { link: input.link })).data
  } catch (error) {
    throw toApiError(error)
  }
}

/** My latest timetable imports, including timetables shared in my groups. */
export async function getImports(): Promise<TimetableImport[]> {
  try {
    return (await api.get<TimetableImport[]>('/timetable/imports/')).data
  } catch (error) {
    throw toApiError(error)
  }
}

export async function getImport(id: number): Promise<TimetableImport> {
  try {
    return (await api.get<TimetableImport>(`/timetable/imports/${id}/`)).data
  } catch (error) {
    throw toApiError(error)
  }
}

/** Show another tab of the file. */
export async function chooseImportTab(id: number, tab: string): Promise<TimetableImport> {
  try {
    return (await api.patch<TimetableImport>(`/timetable/imports/${id}/`, { tab })).data
  } catch (error) {
    throw toApiError(error)
  }
}

/** Save the classes (only `rows`, if given) and add me to them. */
export async function confirmImport(id: number, rows: ImportRow[]): Promise<TimetableImport> {
  try {
    return (await api.post<TimetableImport>(`/timetable/imports/${id}/confirm/`, { rows })).data
  } catch (error) {
    throw toApiError(error)
  }
}

/** "Not my timetable": nothing is saved. */
export async function discardImport(id: number): Promise<TimetableImport> {
  try {
    return (await api.post<TimetableImport>(`/timetable/imports/${id}/discard/`)).data
  } catch (error) {
    throw toApiError(error)
  }
}

/** Changes to my classes from today on (answered or not). */
export async function getChanges(): Promise<ClassChange[]> {
  try {
    return (await api.get<ClassChange[]>('/timetable/changes/')).data
  } catch (error) {
    throw toApiError(error)
  }
}

/** My answer to a change: it changes only my own timetable, and I can change my mind. */
export async function answerChange(id: number, answer: 'confirm' | 'reject'): Promise<ClassChange> {
  try {
    return (await api.post<ClassChange>(`/timetable/changes/${id}/${answer}/`)).data
  } catch (error) {
    throw toApiError(error)
  }
}
