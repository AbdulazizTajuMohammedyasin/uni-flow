import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import {
  addSectionByHand,
  answerChange,
  chooseImportTab,
  confirmImport,
  discardImport,
  getChanges,
  getImport,
  getMySections,
  getSections,
  getToday,
  getWeek,
  joinSection,
  leaveSection,
  startImport,
} from '@/api/timetable'
import type { AddSectionData, ImportRow } from '@/types/timetable'

// Every timetable query starts with 'timetable', so one invalidation refreshes them all.
export const timetableKeys = {
  all: ['timetable'] as const,
  today: ['timetable', 'today'] as const,
  week: (date: string | undefined) => ['timetable', 'week', date ?? 'this'] as const,
  mySections: ['timetable', 'my-sections'] as const,
  sections: (search: string) => ['timetable', 'sections', search] as const,
  timetableImport: (id: number) => ['timetable', 'import', id] as const,
  changes: ['timetable', 'changes'] as const,
}

export function useToday() {
  return useQuery({ queryKey: timetableKeys.today, queryFn: getToday })
}

export function useWeek(date: string | undefined) {
  return useQuery({ queryKey: timetableKeys.week(date), queryFn: () => getWeek(date) })
}

export function useMySections() {
  return useQuery({ queryKey: timetableKeys.mySections, queryFn: getMySections })
}

export function useSectionSearch(search: string) {
  return useQuery({ queryKey: timetableKeys.sections(search), queryFn: () => getSections(search) })
}

/** Join, leave and add-by-hand all change "my timetable": refresh everything after. */
function useTimetableChange<Input, Result>(change: (input: Input) => Promise<Result>) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: change,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: timetableKeys.all }),
  })
}

export const useJoinSection = () => useTimetableChange((id: number) => joinSection(id))
export const useLeaveSection = () => useTimetableChange((id: number) => leaveSection(id))
export const useAddSection = () =>
  useTimetableChange((data: AddSectionData) => addSectionByHand(data))

/** One "Add my timetable" import; checked every 2 seconds while the AI is reading it. */
export function useTimetableImport(id: number | null) {
  return useQuery({
    queryKey: timetableKeys.timetableImport(id ?? 0),
    queryFn: () => getImport(id as number),
    enabled: id !== null,
    refetchInterval: (query) => (query.state.data?.status === 'reading' ? 2000 : false),
  })
}

export const useStartImport = () =>
  useTimetableChange((input: { file: File } | { link: string }) => startImport(input))
export const useChooseImportTab = () =>
  useTimetableChange(({ id, tab }: { id: number; tab: string }) => chooseImportTab(id, tab))
export const useConfirmImport = () =>
  useTimetableChange(({ id, rows }: { id: number; rows: ImportRow[] }) => confirmImport(id, rows))
export const useDiscardImport = () => useTimetableChange((id: number) => discardImport(id))

export function useClassChanges() {
  return useQuery({ queryKey: timetableKeys.changes, queryFn: getChanges })
}

/** Confirm or reject a change; today and the week are refreshed to show it. */
export const useAnswerChange = () =>
  useTimetableChange(({ id, answer }: { id: number; answer: 'confirm' | 'reject' }) =>
    answerChange(id, answer),
  )
