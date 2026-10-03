import type { Meeting } from '@/types/timetable'

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

/** "2026-03-30" plus `days` days, as YYYY-MM-DD. */
export function shiftDate(isoDate: string, days: number): string {
  const date = new Date(`${isoDate}T00:00:00Z`)
  date.setUTCDate(date.getUTCDate() + days)
  return date.toISOString().slice(0, 10)
}
