/** Shared fake data for page tests. */
import type { Intake, Programme, School } from '@/types/academics'
import type { User } from '@/types/auth'

export const schools: School[] = [
  { id: 1, code: 'SCI', name: 'School of Computing and Informatics' },
  { id: 2, code: 'SBSS', name: 'School of Business & Social Sciences' },
]

export const programmes: Programme[] = [
  { id: 10, code: 'BCS', name: 'Bachelor in Computer Science (Honours)', level: 'bachelor', level_label: 'Bachelor', school: 1 },
  { id: 11, code: 'BDS', name: 'Bachelor in Data Science (Honours)', level: 'bachelor', level_label: 'Bachelor', school: 1 },
  { id: 20, code: 'BBA', name: 'Bachelor of Business Administration (Honours)', level: 'bachelor', level_label: 'Bachelor', school: 2 },
]

export const intakes: Intake[] = [
  { id: 100, code: '2025-OCT', name: 'October 2025', start_date: '2025-10-01' },
  { id: 101, code: '2025-MAR', name: 'March 2025', start_date: '2025-03-01' },
]

export function makeStudent(overrides: Partial<User> = {}): User {
  return {
    id: 1,
    email: 'ali@student.aiu.edu.my',
    full_name: 'Ali Hassan',
    role: 'student',
    profile_complete: false,
    student_profile: { student_number: null, school: null, programme: null, intake: null },
    staff_profile: null,
    ...overrides,
  }
}
