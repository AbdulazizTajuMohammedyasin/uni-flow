import { useState } from 'react'
import {
  AtSign,
  CalendarClock,
  CalendarX,
  CircleAlert,
  Info,
  Megaphone,
  Newspaper,
  type LucideIcon,
} from 'lucide-react'
import { useNavigate } from 'react-router'

import { EmptyState } from '@/components/EmptyState'
import { ErrorState } from '@/components/ErrorState'
import { ListSkeleton } from '@/components/ListSkeleton'
import { PageHeader } from '@/components/PageHeader'
import { Button } from '@/components/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import {
  useMarkAllNotificationsRead,
  useMarkNotificationRead,
  useNotifications,
} from '@/hooks/useNotifications'
import { groupByDay, KIND_LABELS, NEEDS_YOU_KINDS, notificationLink, timeAgo } from '@/lib/notifications'
import { cn } from '@/lib/utils'
import type { AppNotification, NotificationKind } from '@/types/notifications'

const KIND_ICONS: Record<NotificationKind, LucideIcon> = {
  direct_attention: AtSign,
  action_required: CircleAlert,
  important_update: Megaphone,
  timetable_change_proposed: CalendarClock,
  timetable_change_retracted: CalendarX,
  digest: Newspaper,
  system: Info,
}

type Tab = 'all' | 'needs-you'
// The panel itself takes keyboard focus (after the tabs), so it needs a visible ring.
const PANEL = 'rounded-xl focus-visible:ring-3 focus-visible:ring-ring/50 focus-visible:ring-offset-4 focus-visible:ring-offset-background'

/** /notifications — my alerts, newest first and split by day. "Needs you" keeps only the
 * ones that ask something of me. Tapping one marks it read and opens it. */
export function NotificationsPage() {
  const notifications = useNotifications()
  const markAll = useMarkAllNotificationsRead()
  const [tab, setTab] = useState<Tab>('all')
  const hasUnread = notifications.data?.some((notification) => !notification.read)
  const needsYou = notifications.data?.filter((notification) => NEEDS_YOU_KINDS.has(notification.kind)) ?? []

  return (
    <div className="max-w-3xl space-y-6">
      <PageHeader
        title="Notifications"
        actions={
          hasUnread && (
            <Button size="sm" variant="outline" disabled={markAll.isPending} onClick={() => markAll.mutate()}>
              Mark all as read
            </Button>
          )
        }
      />

      {notifications.isPending ? (
        <ListSkeleton />
      ) : notifications.isError ? (
        <ErrorState title="Could not load your notifications" />
      ) : notifications.data.length === 0 ? (
        <EmptyState
          title="No notifications yet"
          description="UniFlow alerts you when you're named, need to act, or something important changes for you, plus a digest every evening."
        />
      ) : (
        <Tabs value={tab} onValueChange={(value) => setTab(value as Tab)} className="gap-5">
          <TabsList className="w-full sm:w-fit group-data-horizontal/tabs:h-auto">
            <TabsTrigger value="all" className="h-11 px-4 md:h-8">
              All
            </TabsTrigger>
            <TabsTrigger value="needs-you" className="h-11 px-4 md:h-8">
              Needs you ({needsYou.length})
            </TabsTrigger>
          </TabsList>
          <TabsContent value="all" className={PANEL}>
            <DayGroups notifications={notifications.data} />
          </TabsContent>
          <TabsContent value="needs-you" className={PANEL}>
            {needsYou.length === 0 ? (
              <EmptyState
                title="Nothing needs you"
                description="Alerts where you're named, need to act, or have a class change to confirm show up here."
              />
            ) : (
              <DayGroups notifications={needsYou} />
            )}
          </TabsContent>
        </Tabs>
      )}
    </div>
  )
}

function DayGroups({ notifications }: { notifications: AppNotification[] }) {
  return (
    <div className="space-y-6">
      {groupByDay(notifications).map((group) => (
        <section key={group.label} aria-label={group.label} className="space-y-2">
          <h2 className="text-sm font-medium text-muted-foreground">{group.label}</h2>
          <ul className="divide-y divide-border overflow-hidden rounded-xl bg-card ring-1 ring-border">
            {group.notifications.map((notification) => (
              <NotificationRow key={notification.id} notification={notification} />
            ))}
          </ul>
        </section>
      ))}
    </div>
  )
}

function NotificationRow({ notification }: { notification: AppNotification }) {
  const markRead = useMarkNotificationRead()
  const navigate = useNavigate()
  const link = notificationLink(notification)
  const Icon = KIND_ICONS[notification.kind]
  const unread = !notification.read

  function open() {
    if (unread) markRead.mutate(notification.id)
    if (link) navigate(link)
  }

  return (
    <li>
      <button
        type="button"
        onClick={open}
        className={cn(
          'flex w-full gap-3 px-4 py-3.5 text-left outline-none hover:bg-muted/60 focus-visible:bg-muted/60 focus-visible:ring-3 focus-visible:ring-ring/50 focus-visible:ring-inset',
          unread && 'bg-accent/50',
        )}
      >
        <span
          className={cn(
            'mt-0.5 flex size-8 shrink-0 items-center justify-center rounded-full',
            unread ? 'bg-primary/25 text-foreground' : 'bg-muted text-muted-foreground',
          )}
        >
          <Icon aria-hidden className="size-4" />
        </span>
        <span className="min-w-0 flex-1 space-y-0.5">
          {/* Unread: the word "New", a dot and a bold title, not colour alone. */}
          <span className="flex items-center gap-1 text-xs font-medium text-muted-foreground">
            {unread && (
              <span className="inline-flex items-center gap-1 font-medium text-foreground">
                <span aria-hidden className="size-1.5 rounded-full bg-primary" />
                New ·
              </span>
            )}
            <span>
              {KIND_LABELS[notification.kind]} · {timeAgo(notification.created_at)}
            </span>
          </span>
          <span className={cn('block leading-snug text-foreground', unread ? 'font-medium' : 'font-normal')}>
            {notification.title}
          </span>
          {notification.body && <span className="block text-sm text-muted-foreground">{notification.body}</span>}
        </span>
      </button>
    </li>
  )
}
