/** GET /api/v1/auth/users/me/ */
export type User = {
  id: number
  email: string
  full_name: string
  role: 'student' | 'lecturer' | 'school_staff' | 'university_admin' | 'super_admin'
  profile_complete: boolean
  student_profile: {
    student_number: string | null
    school: number | null
    programme: number | null
    intake: number | null
  } | null
  staff_profile: {
    school: number | null
    position_title: string
  } | null
}

export type LoginData = {
  email: string
  password: string
}

export type RegisterData = {
  full_name: string
  email: string
  password: string
  re_password: string
}
