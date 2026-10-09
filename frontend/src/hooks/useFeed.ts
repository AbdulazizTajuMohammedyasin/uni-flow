import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { getFeed, getFeedItem, updateFeedItem } from '@/api/feed'

// Every feed query starts with 'feed', so one invalidation refreshes them all.
export const feedKeys = {
  all: ['feed'] as const,
  list: ['feed', 'list'] as const,
  item: (id: number) => ['feed', 'item', id] as const,
}

export function useFeed() {
  return useQuery({ queryKey: feedKeys.list, queryFn: getFeed })
}

export function useFeedItem(id: number) {
  return useQuery({ queryKey: feedKeys.item(id), queryFn: () => getFeedItem(id) })
}

/** Read, dismiss or "not relevant": the feed list is refreshed afterwards. */
export function useUpdateFeedItem() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, action }: { id: number; action: 'read' | 'dismiss' | 'not_relevant' }) =>
      updateFeedItem(id, action),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: feedKeys.list }),
  })
}
