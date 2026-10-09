import type { FeedDetail, FeedItem } from '@/types/feed'
import type { Page } from '@/types/timetable'

import { api } from './client'
import { toApiError } from './errors'

/** My feed, all levels (Direct attention first). 100 items is plenty for the pilot. */
export async function getFeed(): Promise<FeedItem[]> {
  try {
    return (await api.get<Page<FeedItem>>('/feed/', { params: { page_size: 100 } })).data.results
  } catch (error) {
    throw toApiError(error)
  }
}

export async function getFeedItem(id: number): Promise<FeedDetail> {
  try {
    return (await api.get<FeedDetail>(`/feed/${id}/`)).data
  } catch (error) {
    throw toApiError(error)
  }
}

/** Read, dismiss (hide from my feed) or "not relevant to me" (hide and remember). */
export async function updateFeedItem(id: number, action: 'read' | 'dismiss' | 'not_relevant'): Promise<void> {
  try {
    if (action === 'not_relevant') {
      await api.post(`/feed/${id}/feedback/`, { feedback: 'not_relevant' })
    } else {
      await api.post(`/feed/${id}/${action}/`)
    }
  } catch (error) {
    throw toApiError(error)
  }
}
