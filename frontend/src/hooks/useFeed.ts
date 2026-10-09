import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { getDigest, getFeed, getFeedItem, getHome, searchFeed, updateFeedItem } from '@/api/feed'

// Every feed query starts with 'feed', so one invalidation refreshes them all.
export const feedKeys = {
  all: ['feed'] as const,
  list: ['feed', 'list'] as const,
  home: ['feed', 'home'] as const,
  search: (q: string) => ['feed', 'search', q] as const,
  item: (id: number) => ['feed', 'item', id] as const,
  digest: (date: string | undefined) => ['feed', 'digest', date ?? 'latest'] as const,
}

export function useFeed() {
  return useQuery({ queryKey: feedKeys.list, queryFn: getFeed })
}

export function useHome() {
  return useQuery({ queryKey: feedKeys.home, queryFn: getHome })
}

/** Only asks the server once there are at least 2 characters. */
export function useSearch(q: string) {
  return useQuery({ queryKey: feedKeys.search(q), queryFn: () => searchFeed(q), enabled: q.length >= 2 })
}

export function useDigest(date: string | undefined) {
  return useQuery({ queryKey: feedKeys.digest(date), queryFn: () => getDigest(date) })
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
    onSuccess: () => queryClient.invalidateQueries({ queryKey: feedKeys.all }),
  })
}
