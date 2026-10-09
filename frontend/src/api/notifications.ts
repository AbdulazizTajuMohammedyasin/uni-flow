import type { AppNotification } from '@/types/notifications'
import type { Page } from '@/types/timetable'

import { api } from './client'
import { toApiError } from './errors'

/** My latest alerts, newest first. */
export async function getNotifications(): Promise<AppNotification[]> {
  try {
    const params = { page_size: 50 }
    return (await api.get<Page<AppNotification>>('/notifications/', { params })).data.results
  } catch (error) {
    throw toApiError(error)
  }
}

/** How many alerts I haven't read (the number on the bell). */
export async function getUnreadCount(): Promise<number> {
  try {
    return (await api.get<{ count: number }>('/notifications/unread-count/')).data.count
  } catch (error) {
    throw toApiError(error)
  }
}

export async function markNotificationRead(id: number): Promise<void> {
  try {
    await api.post(`/notifications/${id}/read/`)
  } catch (error) {
    throw toApiError(error)
  }
}

export async function markAllNotificationsRead(): Promise<void> {
  try {
    await api.post('/notifications/read-all/')
  } catch (error) {
    throw toApiError(error)
  }
}
