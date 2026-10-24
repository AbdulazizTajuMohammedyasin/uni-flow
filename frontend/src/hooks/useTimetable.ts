import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import {
  addSectionByHand,
  answerChange,
  chooseImportTab,
  confirmImport,
  discardImport,
  getChanges,
  getImport,
  getImports,
  getMySections,
  getSections,
  getSemesters,
  getToday,
  getWeek,
  joinSection,
  leaveSection,
  moveSections,
  startImport,
} from '@/api/timetable'
import type { AddSectionData, ImportRow, SemesterChoice } from '@/types/timetable'

// Every timetable query starts with 'timetable', so one invalidation refreshes them all.
export const timetableKeys = {
  all: ['timetable'] as const,
  today: ['timetable', 'today'] as const,
  week: (date: string | undefined) => ['timetable', 'week', date ?? 'this'] as const,
  mySections: ['timetable', 'my-sections'] as const,
  sections: (search: string, semester: SemesterChoice) => ['timetable', 'sections', semester, search] as const,
  semesters: ['timetable', 'semesters'] as const,
  timetableImport: (id: number) => ['timetable', 'import', id] as const,
  imports: ['timetable', 'imports'] as const,
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

export function useSectionSearch(search: string, semester: SemesterChoice = 'current') {
  return useQuery({
    queryKey: timetableKeys.sections(search, semester),
    queryFn: () => getSections(search, semester),
  })
}

export function useSemesters() {
  return useQuery({ queryKey: timetableKeys.semesters, queryFn: getSemesters })
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
export const useMoveSections = () => useTimetableChange((fromTerm: number) => moveSections(fromTerm))
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

export function useTimetableImports() {
  return useQuery({ queryKey: timetableKeys.imports, queryFn: getImports })
}

export const useStartImport = () =>
  useTimetableChange(
    ({ input, semester }: { input: { file: File } | { link: string }; semester: SemesterChoice }) =>
      startImport(input, semester),
  )
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
