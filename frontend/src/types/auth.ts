/** What a user may manage (the backend decides; see apps/accounts/capabilities.py). */
export type Capability =
  | 'announcements.manage'
  | 'events.manage'
  | 'documents.manage'
  | 'applications.manage'
  | 'communities.manage'
  | 'timetable.manage'
  | 'academics.manage'
  | 'users.manage'

/** Who a user may publish as: the university, or one school. */
export type Publisher = {
  type: 'university' | 'school'
  id: number | null
  name: string
}

/** The student part of "my profile". */
export type StudentProfile = {
  student_number: string | null
  school: number | null
  programme: number | null
  intake: number | null
  /** Worked out by the backend from the intake and AIU's terms (read-only). */
  current_semester: number | null
  /** Set only when the worked-out semester is wrong. */
  semester_override: number | null
  interests: string[]
  info_types: string[]
  /** Nicknames, comma-separated (used to notice when someone mentions the student). */
  aliases: string
}

/** One option of a picker, e.g. { value: 'ai', label: 'Artificial Intelligence' }. */
export type Choice = {
  value: string
  label: string
}

/** GET /api/v1/auth/preferences/choices/ */
export type PreferenceChoices = {
  interests: Choice[]
  info_types: Choice[]
}

/** GET /api/v1/auth/users/me/ */
export type User = {
  id: number
  email: string
  full_name: string
  role: 'student' | 'lecturer' | 'school_staff' | 'university_admin' | 'super_admin'
  profile_complete: boolean
  student_profile: StudentProfile | null
  staff_profile: {
    school: number | null
    position_title: string
  } | null
  capabilities: Record<Capability, boolean>
  publishers: Publisher[]
}

export type LoginData = {
  email: string
  password: string
}

/** PATCH /api/v1/auth/users/me/ (send only what changes) */
export type UpdateMeData = {
  full_name?: string
  student_profile?: Partial<Omit<StudentProfile, 'current_semester'>>
}

export type ChangePasswordData = {
  current_password: string
  new_password: string
  re_new_password: string
}

export type RegisterData = {
  full_name: string
  email: string
  password: string
  re_password: string
}
