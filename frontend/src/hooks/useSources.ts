import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { createSource, getMySources, pasteMessages, uploadExport } from '@/api/sources'

const mySourcesKey = ['sources', 'mine'] as const

export function useMySources() {
  return useQuery({ queryKey: mySourcesKey, queryFn: getMySources })
}

/** After any change, reload "my groups" (names and message counts). */
function useSourcesChange<Input, Result>(change: (input: Input) => Promise<Result>) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: change,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: mySourcesKey }),
  })
}

export const useCreateSource = () => useSourcesChange((title: string) => createSource(title))
export const usePasteMessages = () =>
  useSourcesChange(({ id, text }: { id: number; text: string }) => pasteMessages(id, text))
export const useUploadExport = () =>
  useSourcesChange(({ id, file }: { id: number; file: File }) => uploadExport(id, file))
