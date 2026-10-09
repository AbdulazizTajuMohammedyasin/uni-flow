import { useNavigate } from 'react-router'

import { EmptyState } from '@/components/EmptyState'
import { ErrorState } from '@/components/ErrorState'
import { PageLoading } from '@/components/PageLoading'
import { Button } from '@/components/ui/button'
import {
  useMarkAllNotificationsRead,
  useMarkNotificationRead,
  useNotifications,
} from '@/hooks/useNotifications'
import { KIND_LABELS, notificationLink, timeAgo } from '@/lib/notifications'
import type { AppNotification } from '@/types/notifications'

/** /notifications — my alerts, newest first. Tapping one marks it read and opens it. */
export function NotificationsPage() {
  const notifications = useNotifications()
  const markAll = useMarkAllNotificationsRead()
  const hasUnread = notifications.data?.some((notification) => !notification.read)

  return (
    <div className="max-w-3xl space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-2xl font-bold tracking-tight">Notifications</h1>
        {hasUnread && (
          <Button size="sm" variant="outline" disabled={markAll.isPending} onClick={() => markAll.mutate()}>
            Mark all as read
          </Button>
        )}
      </div>

      {notifications.isPending ? (
        <PageLoading />
      ) : notifications.isError ? (
        <ErrorState title="Could not load your notifications" />
      ) : notifications.data.length === 0 ? (
        <EmptyState
          title="No notifications yet"
          description="UniFlow alerts you when you're named, need to act, or something important changes for you, plus a digest every evening."
        />
      ) : (
        <ul className="divide-y divide-border rounded-2xl bg-card shadow-sm ring-1 ring-border">
          {notifications.data.map((notification) => (
            <NotificationRow key={notification.id} notification={notification} />
          ))}
        </ul>
      )}
    </div>
  )
}

function NotificationRow({ notification }: { notification: AppNotification }) {
  const markRead = useMarkNotificationRead()
  const navigate = useNavigate()
  const link = notificationLink(notification)

  function open() {
    if (!notification.read) markRead.mutate(notification.id)
    if (link) navigate(link)
  }

  return (
    <li>
      <button
        type="button"
        onClick={open}
        className={`flex w-full gap-3 p-4 text-left hover:bg-muted/50 ${notification.read ? '' : 'bg-brand-50/60'}`}
      >
        <span
          aria-hidden
          className={`mt-1.5 size-2 shrink-0 rounded-full ${notification.read ? 'bg-transparent' : 'bg-primary'}`}
        />
        <span className="min-w-0 space-y-0.5">
          <span className="block text-xs font-medium text-muted-foreground">
            {KIND_LABELS[notification.kind]} · {timeAgo(notification.created_at)}
          </span>
          <span className={`block ${notification.read ? '' : 'font-semibold'}`}>{notification.title}</span>
          {notification.body && <span className="block text-sm text-muted-foreground">{notification.body}</span>}
        </span>
      </button>
    </li>
  )
}
