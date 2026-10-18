import type { ChangeFlag, ClassChange, Meeting } from '@/types/timetable'

/** "Mon 10:00–12:00 · B2" */
export function meetingText(meeting: Meeting): string {
  const place = [meeting.building, meeting.room].filter(Boolean).join(' ')
  const time = `${meeting.weekday_label.slice(0, 3)} ${meeting.start_time.slice(0, 5)}–${meeting.end_time.slice(0, 5)}`
  return place ? `${time} · ${place}` : time
}

/** "2026-03-30" -> "Monday 30 Mar" (dates from the API are already Kuala Lumpur dates). */
export function formatDay(isoDate: string): string {
  return new Date(`${isoDate}T00:00:00Z`).toLocaleDateString('en-GB', {
    weekday: 'long',
    day: 'numeric',
    month: 'short',
    timeZone: 'UTC',
  })
}

/** The time now in Malaysia (UniFlow's time zone) as "HH:MM", to compare with class times. */
export function nowInMalaysia(now: Date = new Date()): string {
  return now.toLocaleTimeString('en-GB', {
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
    timeZone: 'Asia/Kuala_Lumpur',
  })
}

/** Today's date in Malaysia as YYYY-MM-DD (the format the timetable API uses). */
export function todayIsoInMalaysia(now: Date = new Date()): string {
  return now.toLocaleDateString('en-CA', { timeZone: 'Asia/Kuala_Lumpur' })
}

/** Today's date in Malaysia, e.g. "Monday 19 October". */
export function todayInMalaysia(now: Date = new Date()): string {
  return now.toLocaleDateString('en-GB', {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
    timeZone: 'Asia/Kuala_Lumpur',
  })
}

/** "2026-03-30" plus `days` days, as YYYY-MM-DD. */
export function shiftDate(isoDate: string, days: number): string {
  const date = new Date(`${isoDate}T00:00:00Z`)
  date.setUTCDate(date.getUTCDate() + days)
  return date.toISOString().slice(0, 10)
}

/** The label on a changed class in Today/Week. */
export function changeLabel(change: ChangeFlag): string {
  if (change.status === 'pending') return 'Change waiting'
  return {
    class_moved: 'Moved',
    class_cancelled: 'Cancelled',
    room_changed: 'Room changed',
    extra_session: 'Extra class',
  }[change.kind]
}

/** What a change does, e.g. "10:00–12:00 → 14:00–16:00" or "Room B2 → C3". */
export function changeText(change: ClassChange): string {
  const was = change.old_start ? `${change.old_start}–${change.old_end}` : ''
  const now = change.new_start ? `${change.new_start}–${change.new_end ?? ''}` : ''
  const room = change.new_room ? ` · ${change.new_room}` : ''
  switch (change.kind) {
    case 'class_cancelled':
      return was ? `${was} class cancelled` : 'Class cancelled'
    case 'room_changed':
      return `Room ${change.old_room || '?'} → ${change.new_room}`
    case 'extra_session':
      return `Extra class ${now}${room}`.trim()
    case 'class_moved':
      if (change.new_date) return `Moved to ${formatDay(change.new_date)} ${now || was}${room}`
      return `${was || 'Class'} → ${now || 'a new time'}${room}`
  }
}
