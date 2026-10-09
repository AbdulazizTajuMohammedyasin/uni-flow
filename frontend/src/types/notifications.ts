/** Shapes of the notifications API (/api/v1/notifications/). */

export type NotificationKind =
  | 'direct_attention'
  | 'action_required'
  | 'important_update'
  | 'timetable_change_proposed'
  | 'timetable_change_retracted'
  | 'digest'
  | 'system'

/** One alert. target_type + target_id say what it opens (e.g. "insight", 42). */
export type AppNotification = {
  id: number
  kind: NotificationKind
  title: string
  body: string
  target_type: string
  target_id: number | null
  read: boolean
  created_at: string
}
