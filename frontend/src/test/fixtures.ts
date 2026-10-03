/** Shared fake data for page tests. */
import type { Intake, Programme, School } from '@/types/academics'
import type { Capability, PreferenceChoices, StudentProfile, User } from '@/types/auth'

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

export const preferenceChoices: PreferenceChoices = {
  interests: [
    { value: 'ai', label: 'Artificial Intelligence' },
    { value: 'cybersecurity', label: 'Cybersecurity' },
  ],
  info_types: [
    { value: 'internship', label: 'Internships' },
    { value: 'bootcamp', label: 'Bootcamps' },
  ],
}

/** A student profile with nothing chosen yet, plus any `overrides`. */
export function makeStudentProfile(overrides: Partial<StudentProfile> = {}): StudentProfile {
  return {
    student_number: null,
    school: null,
    programme: null,
    intake: null,
    current_semester: null,
    semester_override: null,
    interests: [],
    info_types: [],
    aliases: '',
    ...overrides,
  }
}

export function makeStudent(overrides: Partial<User> = {}): User {
  return {
    id: 1,
    email: 'ali@student.aiu.edu.my',
    full_name: 'Ali Hassan',
    role: 'student',
    profile_complete: false,
    student_profile: makeStudentProfile(),
    staff_profile: null,
    capabilities: capabilitiesOf([]),
    publishers: [],
    ...overrides,
  }
}

/** Every capability false, except the ones listed. */
export function capabilitiesOf(granted: Capability[]): Record<Capability, boolean> {
  const all: Capability[] = [
    'announcements.manage',
    'events.manage',
    'documents.manage',
    'applications.manage',
    'communities.manage',
    'timetable.manage',
    'academics.manage',
    'users.manage',
  ]
  return Object.fromEntries(all.map((name) => [name, granted.includes(name)])) as Record<
    Capability,
    boolean
  >
}

/** A school staff member of School 1 (content capabilities, no academics/users). */
export function makeSchoolStaff(overrides: Partial<User> = {}): User {
  return {
    id: 2,
    email: 'lee@aiu.edu.my',
    full_name: 'Dr Lee',
    role: 'school_staff',
    profile_complete: true,
    student_profile: null,
    staff_profile: { school: 1, position_title: 'Lecturer' },
    capabilities: capabilitiesOf([
      'announcements.manage',
      'events.manage',
      'documents.manage',
      'applications.manage',
      'communities.manage',
      'timetable.manage',
    ]),
    publishers: [{ type: 'school', id: 1, name: 'School of Computing and Informatics' }],
    ...overrides,
  }
}
