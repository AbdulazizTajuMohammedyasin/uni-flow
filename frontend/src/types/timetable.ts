/** Shapes of the timetable API (/api/v1/timetable/). */

export type MeetingType = 'lecture' | 'tutorial' | 'lab' | 'other'

export type Meeting = {
  weekday: number // 0 = Monday … 6 = Sunday
  weekday_label: string
  start_time: string // "10:00:00"
  end_time: string
  meeting_type: MeetingType
  building: string
  room: string
}

/** A section with its course and weekly classes. */
export type Section = {
  id: number
  course: { id: number; code: string; name: string }
  code: string
  term: number
  lecturer_name: string
  source: 'ai_import' | 'student' | 'admin' | 'file_import'
  meetings: Meeting[]
}

/** One class on one day (today/week). */
export type ClassSlot = {
  section_id: number
  course_code: string
  course_name: string
  section_code: string
  lecturer_name: string
  start_time: string // "10:00"
  end_time: string
  meeting_type: MeetingType
  building: string
  room: string
}

/** GET timetable/today/ (one day) and timetable/week/ (Monday to Sunday). */
export type TimetableDays = {
  term: { id: number; name: string } | null
  days: { date: string; weekday: number; classes: ClassSlot[] }[]
}

export type NewMeeting = {
  weekday: number
  start_time: string
  end_time: string
  meeting_type: MeetingType
  building: string
  room: string
}

/** POST timetable/sections/ — add a class that is not in UniFlow yet. */
export type AddSectionData = {
  course_code: string
  course_name: string
  section: string
  meetings: NewMeeting[]
}

/** A page of a list (Django REST framework's page format). */
export type Page<T> = {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}
