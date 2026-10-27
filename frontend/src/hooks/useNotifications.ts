import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import {
  getNotifications,
  getPushSettings,
  getUnreadCount,
  markAllNotificationsRead,
  markNotificationRead,
  updatePushSettings,
} from '@/api/notifications'
import type { PushSettings } from '@/types/notifications'

// Every notifications query starts with 'notifications', so one invalidation refreshes all.
export const notificationKeys = {
  all: ['notifications'] as const,
  list: ['notifications', 'list'] as const,
  unread: ['notifications', 'unread'] as const,
  pushSettings: ['notifications', 'push-settings'] as const,
}

const MINUTE = 60_000

/** The bell's number: asked again every 60 s, only while the tab is visible (TanStack
 * Query pauses the timer in a background tab) and when the user comes back to it. */
export function useUnreadCount() {
  return useQuery({
    queryKey: notificationKeys.unread,
    queryFn: getUnreadCount,
    refetchInterval: MINUTE,
    refetchIntervalInBackground: false,
  })
}

export function useNotifications() {
  return useQuery({ queryKey: notificationKeys.list, queryFn: getNotifications })
}

function useNotificationsChange<Input>(change: (input: Input) => Promise<void>) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: change,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: notificationKeys.all }),
  })
}

export const useMarkNotificationRead = () => useNotificationsChange((id: number) => markNotificationRead(id))
export const useMarkAllNotificationsRead = () => useNotificationsChange(() => markAllNotificationsRead())

/** Which alerts reach my phone (shown on Profile inside the app). */
export function usePushSettings() {
  return useQuery({ queryKey: notificationKeys.pushSettings, queryFn: getPushSettings })
}

export function useUpdatePushSettings() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (change: Partial<PushSettings>) => updatePushSettings(change),
    onSuccess: (settings) => queryClient.setQueryData(notificationKeys.pushSettings, settings),
  })
}
