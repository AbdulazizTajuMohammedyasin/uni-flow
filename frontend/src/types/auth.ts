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

/** PATCH /api/v1/auth/users/me/ (send only what changes) */
export type UpdateMeData = {
  full_name?: string
  student_profile?: {
    student_number?: string | null
    school?: number | null
    programme?: number | null
    intake?: number | null
  }
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
