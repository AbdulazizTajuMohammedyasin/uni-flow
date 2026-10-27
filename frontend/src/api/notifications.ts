import type { AppNotification, PushSettings } from '@/types/notifications'
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

/** This phone (the UniFlow app) can get my alerts. `token` is its Expo push address. */
export async function registerDevice(device: {
  token: string
  platform: 'android' | 'ios'
  app_version: string
}): Promise<void> {
  try {
    await api.post('/notifications/devices/', device)
  } catch (error) {
    throw toApiError(error)
  }
}

/** I'm logging out on this phone: it stops getting my alerts. */
export async function unregisterDevice(token: string): Promise<void> {
  try {
    await api.post('/notifications/devices/unregister/', { token })
  } catch (error) {
    throw toApiError(error)
  }
}

export async function getPushSettings(): Promise<PushSettings> {
  try {
    return (await api.get<PushSettings>('/notifications/push-settings/')).data
  } catch (error) {
    throw toApiError(error)
  }
}

export async function updatePushSettings(change: Partial<PushSettings>): Promise<PushSettings> {
  try {
    return (await api.patch<PushSettings>('/notifications/push-settings/', change)).data
  } catch (error) {
    throw toApiError(error)
  }
}
