import type { AppNotification, NotificationKind } from '@/types/notifications'

const MINUTE = 60_000

export const KIND_LABELS: Record<NotificationKind, string> = {
  direct_attention: 'You were named',
  action_required: 'Action required',
  important_update: 'Important update',
  timetable_change_proposed: 'Class change to confirm',
  timetable_change_retracted: 'Class change taken back',
  digest: 'Daily digest',
  system: 'From UniFlow',
}

/** Where an alert goes when tapped: its item, or that day's digest (target_id 20261009 →
 * /digest?date=2026-10-09). Null when it opens nothing. */
export function notificationLink(notification: AppNotification): string | null {
  const { target_type: type, target_id: id } = notification
  if (id === null) return null
  if (type === 'insight') return `/insights/${id}`
  if (type === 'digest') {
    const day = String(id)
    return `/digest?date=${day.slice(0, 4)}-${day.slice(4, 6)}-${day.slice(6, 8)}`
  }
  return null
}

/** "5 min ago", "3 h ago", or the date for older alerts. */
export function timeAgo(iso: string, now = Date.now()): string {
  const minutes = Math.round((now - new Date(iso).getTime()) / MINUTE)
  if (minutes < 1) return 'just now'
  if (minutes < 60) return `${minutes} min ago`
  if (minutes < 24 * 60) return `${Math.round(minutes / 60)} h ago`
  return new Date(iso).toLocaleDateString('en-GB', {
    day: 'numeric',
    month: 'short',
    timeZone: 'Asia/Kuala_Lumpur',
  })
}


/** The kinds the "Needs you" tab keeps: the student is named, has to act, or has a class
 * change to answer. */
export const NEEDS_YOU_KINDS: ReadonlySet<NotificationKind> = new Set([
  'direct_attention',
  'action_required',
  'timetable_change_proposed',
])

const dayKey = (date: Date) => date.toLocaleDateString('en-CA', { timeZone: 'Asia/Kuala_Lumpur' })

/** "Today", "Yesterday", or "Fri 16 Oct", in Malaysia time. */
export function dayLabel(iso: string, now = Date.now()): string {
  const day = dayKey(new Date(iso))
  if (day === dayKey(new Date(now))) return 'Today'
  if (day === dayKey(new Date(now - 24 * 60 * MINUTE))) return 'Yesterday'
  return new Date(iso).toLocaleDateString('en-GB', {
    weekday: 'short',
    day: 'numeric',
    month: 'short',
    timeZone: 'Asia/Kuala_Lumpur',
  })
}

/** Alerts (already newest first) split into days, keeping their order. */
export function groupByDay(
  notifications: AppNotification[],
  now = Date.now(),
): { label: string; notifications: AppNotification[] }[] {
  const groups: { label: string; notifications: AppNotification[] }[] = []
  for (const notification of notifications) {
    const label = dayLabel(notification.created_at, now)
    const last = groups.at(-1)
    if (last?.label === label) last.notifications.push(notification)
    else groups.push({ label, notifications: [notification] })
  }
  return groups
}
