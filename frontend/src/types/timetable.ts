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

/** A term as students see it. `estimated`: dates worked out from last year's calendar. */
export type Semester = {
  id: number
  name: string
  starts_on: string // "2026-10-26"
  ends_on: string
  estimated: boolean
}

/** Which semester classes are added to. */
export type SemesterChoice = 'current' | 'next'

/** GET timetable/semesters/ — this semester and the next. */
export type Semesters = { current: Semester | null; next: Semester | null }

/** A section with its course, semester and weekly classes. */
export type Section = {
  id: number
  course: { id: number; code: string; name: string }
  code: string
  term: number
  semester: Semester
  lecturer_name: string
  source: 'ai_import' | 'student' | 'admin' | 'file_import'
  meetings: Meeting[]
}

export type ChangeKind = 'class_moved' | 'class_cancelled' | 'room_changed' | 'extra_session'

/** A class change on a class: confirmed (applied) or pending (not answered yet). */
export type ChangeFlag = { id: number; kind: ChangeKind; status: 'confirmed' | 'pending' }

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
  change: ChangeFlag | null
}

/** GET timetable/today/ (one day) and timetable/week/ (Monday to Sunday). */
export type TimetableDays = {
  term: { id: number; name: string; starts_on: string; ends_on: string } | null
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
  semester?: SemesterChoice
}

/** A page of a list (Django REST framework's page format). */
export type Page<T> = {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

/** One class as read from a timetable file (before it is saved). */
export type ImportRow = {
  course_code: string
  course_name: string
  section: string
  lecturer: string
  meetings: { day: string; start: string; end: string; type: string; room: string }[]
}

/** "Is this your timetable?" — GET timetable/imports/{id}/ */
export type TimetableImport = {
  id: number
  status: 'reading' | 'ready' | 'confirmed' | 'discarded' | 'failed'
  file_name: string
  group: string // the group it was shared in; blank for my own upload
  tab: string
  tabs: string[]
  rows: ImportRow[]
  report: {
    created_sections?: string[]
    existing_sections?: string[]
    differences?: string[]
    errors?: string[]
    enrolled?: string[]
  }
  error: string
  created_at: string
}

/** GET timetable/changes/ — a change the AI found in a group message, for my section. */
export type ClassChange = {
  id: number
  kind: ChangeKind
  course_code: string
  course_name: string
  section_code: string
  title: string
  summary: string
  not_confirmed: boolean // the AI wasn't sure
  date: string // the day of the class that changes
  old_start: string | null
  old_end: string | null
  old_room: string | null
  new_date: string | null // moved to another day
  new_start: string | null
  new_end: string | null
  new_room: string
  my_status: 'pending' | 'confirmed' | 'rejected'
  evidence: { quote: string; group: string; sender_name: string; sent_at: string }[]
}
