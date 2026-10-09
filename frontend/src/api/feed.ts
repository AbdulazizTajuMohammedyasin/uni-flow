import type { Digest, FeedDetail, FeedItem, Home } from '@/types/feed'
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

/** The home screen: the urgent levels, today's classes, changes waiting, and more. */
export async function getHome(): Promise<Home> {
  try {
    return (await api.get<Home>('/feed/home/')).data
  } catch (error) {
    throw toApiError(error)
  }
}

/** Everything delivered to me that contains every word of `q` (2+ characters). */
export async function searchFeed(q: string): Promise<FeedItem[]> {
  try {
    return (await api.get<Page<FeedItem>>('/feed/search/', { params: { q, page_size: 50 } })).data.results
  } catch (error) {
    throw toApiError(error)
  }
}

/** One day's daily digest (YYYY-MM-DD), or my latest one. */
export async function getDigest(date?: string): Promise<Digest> {
  try {
    const params = date ? { date } : undefined
    return (await api.get<Digest>('/feed/digest/', { params })).data
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
