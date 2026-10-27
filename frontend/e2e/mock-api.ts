/**
 * A fake UniFlow backend for browser tests and screenshots.
 *
 * Every call to /api/v1/ is answered here from made-up data, so no backend, database or real
 * student is needed. A "scenario" picks which data a page sees:
 * - busy: a student with classes, items, alerts and groups (the main screenshots)
 * - empty: a student who finished onboarding but has nothing yet
 * - error: the main lists fail (500)
 * - loading: the main lists never answer (shows loading states)
 * - new: a student who still has to choose their studies (onboarding)
 * - staff: a school staff member (staff area)
 * - visitor: not logged in
 */
import type { Page, Route } from '@playwright/test'

import type { Intake, Programme, School } from '../src/types/academics'
import type { PreferenceChoices, User } from '../src/types/auth'
import type { Evidence, FeedDetail, FeedItem, Home } from '../src/types/feed'
import type { AppNotification } from '../src/types/notifications'
import type { Source } from '../src/types/sources'
import type { ClassChange, ClassSlot, Section, TimetableDays } from '../src/types/timetable'

export type Scenario = 'busy' | 'empty' | 'error' | 'loading' | 'new' | 'staff' | 'visitor'

/** Monday 19 October 2026, 09:30 in Malaysia: the "now" of every screenshot. */
export const NOW = new Date('2026-10-19T09:30:00+08:00')
const WEEK = ['2026-10-19', '2026-10-20', '2026-10-21', '2026-10-22', '2026-10-23', '2026-10-24', '2026-10-25']

// --- Reference data ------------------------------------------------------------------------

const schools: School[] = [
  { id: 1, code: 'SCI', name: 'School of Computing and Informatics' },
  { id: 2, code: 'SBSS', name: 'School of Business & Social Sciences' },
]
const programmes: Programme[] = [
  { id: 10, code: 'BCS', name: 'Bachelor in Computer Science (Honours)', level: 'bachelor', level_label: 'Bachelor', school: 1 },
  { id: 11, code: 'BDS', name: 'Bachelor in Data Science (Honours)', level: 'bachelor', level_label: 'Bachelor', school: 1 },
]
const intakes: Intake[] = [
  { id: 100, code: '2025-MAR', name: 'March 2025', start_date: '2025-03-01' },
  { id: 101, code: '2025-OCT', name: 'October 2025', start_date: '2025-10-01' },
]
const choices: PreferenceChoices = {
  interests: [
    { value: 'ai', label: 'Artificial Intelligence' },
    { value: 'data_science', label: 'Data Science' },
    { value: 'software_engineering', label: 'Software Engineering' },
    { value: 'cybersecurity', label: 'Cybersecurity' },
  ],
  info_types: [
    { value: 'internship', label: 'Internships' },
    { value: 'competition', label: 'Competitions' },
    { value: 'scholarship', label: 'Scholarships' },
    { value: 'academic_notice', label: 'Academic notices' },
  ],
}

const noCapabilities = {
  'announcements.manage': false,
  'events.manage': false,
  'documents.manage': false,
  'applications.manage': false,
  'communities.manage': false,
  'timetable.manage': false,
  'academics.manage': false,
  'users.manage': false,
}

function student(complete: boolean): User {
  return {
    id: 1,
    email: 'aisha.rahman@student.aiu.edu.my',
    full_name: 'Aisha Rahman',
    role: 'student',
    profile_complete: complete,
    student_profile: {
      student_number: complete ? 'AIU25000001' : null,
      school: complete ? 1 : null,
      programme: complete ? 10 : null,
      intake: complete ? 100 : null,
      current_semester: complete ? 3 : null,
      semester_override: null,
      interests: complete ? ['ai', 'software_engineering'] : [],
      info_types: complete ? ['internship'] : [],
      aliases: complete ? 'Aisha' : '',
    },
    staff_profile: null,
    capabilities: noCapabilities,
    publishers: [],
  }
}

const staff: User = {
  id: 2,
  email: 'daniel.lim@aiu.edu.my',
  full_name: 'Daniel Lim',
  role: 'school_staff',
  profile_complete: true,
  student_profile: null,
  staff_profile: { school: 1, position_title: 'Programme coordinator' },
  capabilities: { ...noCapabilities, 'announcements.manage': true, 'timetable.manage': true },
  publishers: [{ type: 'school', id: 1, name: 'School of Computing and Informatics' }],
}

// --- Timetable -----------------------------------------------------------------------------

const SEMESTER = { id: 1, name: '2026/27 Semester 1', starts_on: '2026-10-12', ends_on: '2027-02-26', estimated: false }
const NEXT_SEMESTER = { id: 2, name: '2026/27 Semester 2', starts_on: '2027-03-22', ends_on: '2027-07-16', estimated: true }

const sections: Section[] = [
  section(1, 'CCS2213', 'Machine Learning', 'C2', 'Dr Farah Aziz', [[0, '08:30', '10:30', 'B09_210'], [2, '14:30', '16:30', 'B09_210']]),
  section(2, 'CCC2113', 'Data Structures and Algorithm Analysis', '1', 'Dr Omar Said', [[0, '11:00', '13:00', 'Lecture Theatre 4'], [3, '08:30', '10:30', 'B09_310']]),
  section(3, 'CCC2213', 'Operating Systems', 'C2', 'Ms Lina Tan', [[1, '10:00', '12:00', 'B09_306'], [4, '14:30', '16:30', 'B09_306']]),
  section(4, 'CCS2223', 'Human Computer Interaction', 'C2', 'Mr Yusuf Ali', [[0, '14:30', '16:30', 'B09_212'], [5, '10:30', '12:30', 'B09_212']]),
]

function section(
  id: number,
  code: string,
  name: string,
  sectionCode: string,
  lecturer: string,
  meetings: [number, string, string, string][],
): Section {
  const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
  return {
    id,
    course: { id: id * 10, code, name },
    code: sectionCode,
    term: 1,
    semester: SEMESTER,
    lecturer_name: lecturer,
    source: 'student',
    meetings: meetings.map(([weekday, start, end, room]) => ({
      weekday,
      weekday_label: days[weekday],
      start_time: `${start}:00`,
      end_time: `${end}:00`,
      meeting_type: 'lecture',
      building: '',
      room,
    })),
  }
}

function slotsFor(weekday: number): ClassSlot[] {
  return sections
    .flatMap((s) =>
      s.meetings
        .filter((m) => m.weekday === weekday)
        .map((m) => ({
          section_id: s.id,
          course_code: s.course.code,
          course_name: s.course.name,
          section_code: s.code,
          lecturer_name: s.lecturer_name,
          start_time: m.start_time.slice(0, 5),
          end_time: m.end_time.slice(0, 5),
          meeting_type: m.meeting_type,
          building: m.building,
          room: m.room,
          change:
            s.id === 2 && weekday === 0
              ? ({ id: 51, kind: 'room_changed', status: 'confirmed' } as const)
              : s.id === 4 && weekday === 0
                ? ({ id: 52, kind: 'class_moved', status: 'pending' } as const)
                : null,
        })),
    )
    .sort((a, b) => a.start_time.localeCompare(b.start_time))
}

function week(withClasses: boolean): TimetableDays {
  return {
    term: { id: 1, name: '2026/27 Semester 1', starts_on: '2026-10-12', ends_on: '2027-02-26' },
    days: WEEK.map((date, weekday) => ({ date, weekday, classes: withClasses ? slotsFor(weekday) : [] })),
  }
}

const changes: ClassChange[] = [
  {
    id: 52,
    kind: 'class_moved',
    course_code: 'CCS2223',
    course_name: 'Human Computer Interaction',
    section_code: 'C2',
    title: 'HCI class moved to Wednesday',
    summary: "Today's HCI class moves to Wednesday 10:00 in B09_212.",
    not_confirmed: false,
    date: '2026-10-19',
    old_start: '14:30',
    old_end: '16:30',
    old_room: 'B09_212',
    new_date: '2026-10-21',
    new_start: '10:00',
    new_end: '12:00',
    new_room: 'B09_212',
    my_status: 'pending',
    can_repeat: true,
    every_week: false,
    evidence: [
      {
        quote: "Class today is moved to Wednesday 10am, same room. Please inform your friends.",
        group: 'CCS2223 HCI – Section C2',
        sender_name: 'Mr Yusuf Ali',
        sent_at: '2026-10-19T07:58:00+08:00',
      },
    ],
  },
]

// --- Feed ----------------------------------------------------------------------------------

function item(id: number, overrides: Partial<FeedItem>): FeedItem {
  return {
    id,
    kind: 'notice',
    info_type: '',
    tier: 'important',
    title: '',
    summary: '',
    importance: 3,
    relevance: 3,
    reason: '',
    action_required: false,
    action_text: '',
    starts_at: null,
    deadline_at: null,
    location: '',
    link: '',
    not_confirmed: false,
    official: false,
    read: false,
    published_at: '2026-10-19T08:00:00+08:00',
    ...overrides,
  }
}

const feed: FeedItem[] = [
  item(101, {
    kind: 'meeting',
    tier: 'direct',
    title: 'Project meeting with Dr Farah',
    summary: 'Aisha and the Machine Learning project group should meet Dr Farah on Tuesday at 15:00 in her office.',
    reason: 'You were named in this message',
    starts_at: '2026-10-20T07:00:00Z',
    location: 'B09 level 2, room 2.14',
  }),
  item(102, {
    kind: 'assignment',
    tier: 'action',
    title: 'Submit HCI usability report',
    summary: 'Upload the group usability report to the course page before the deadline.',
    reason: 'You are in CCS2223 Section C2',
    action_required: true,
    action_text: 'Upload the PDF report on the course page.',
    deadline_at: '2026-10-23T15:59:00Z',
  }),
  item(103, {
    kind: 'class_moved',
    tier: 'important',
    title: 'HCI class moved to Wednesday',
    summary: "Today's HCI class moves to Wednesday 10:00 in B09_212.",
    reason: 'You are in CCS2223 Section C2',
    starts_at: '2026-10-21T02:00:00Z',
  }),
  item(104, {
    kind: 'notice',
    tier: 'important',
    official: true,
    read: true,
    title: 'Mid-semester break dates confirmed',
    summary: 'The mid-semester break runs from 2 to 8 November. Classes resume on 9 November.',
    reason: 'For all SCI students',
  }),
  item(105, {
    kind: 'internship',
    info_type: 'internship',
    tier: 'digest',
    title: 'Software engineering internship at a Kuala Lumpur fintech',
    summary: 'A 3-month internship for computing students from January. Applications close 31 October.',
    reason: 'You are interested in Software Engineering',
    deadline_at: '2026-10-31T15:59:00Z',
    link: 'https://example.com/apply',
  }),
  item(106, {
    kind: 'competition',
    info_type: 'competition',
    tier: 'digest',
    not_confirmed: true,
    title: 'AI hackathon registration open',
    summary: 'Teams of 3–4 can register for the inter-university AI hackathon in November.',
    reason: 'You are interested in Artificial Intelligence',
  }),
]

const evidenceById: Record<number, Evidence[]> = {
  101: [
    {
      group: { id: 1, platform: 'whatsapp_group', title: 'CCS2213 Machine Learning – C2' },
      sender_name: 'Dr Farah Aziz',
      sent_at: '2026-10-19T08:12:00+08:00',
      quote: 'Aisha, Hakim and Mei, please see me on Tuesday 3pm about your project proposal.',
      open_url: '',
    },
  ],
  103: [
    {
      group: { id: 2, platform: 'whatsapp_group', title: 'CCS2223 HCI – Section C2' },
      sender_name: 'Mr Yusuf Ali',
      sent_at: '2026-10-19T07:58:00+08:00',
      quote: 'Class today is moved to Wednesday 10am, same room. Please inform your friends.',
      open_url: '',
    },
  ],
}

function detail(found: FeedItem): FeedDetail {
  return {
    ...found,
    data: {},
    topics: [],
    evidence: evidenceById[found.id] ?? [
      {
        group: { id: 3, platform: 'telegram_channel', title: 'SCI Student Affairs' },
        sender_name: 'SCI Office',
        sent_at: '2026-10-19T08:00:00+08:00',
        quote: found.summary,
        open_url: 'https://t.me/example/1',
      },
    ],
    timetable_change: found.id === 103 ? { id: 52, my_status: 'pending' } : null,
    dismissed: false,
  }
}

const notifications: AppNotification[] = [
  { id: 1, kind: 'timetable_change_proposed', title: 'HCI class moved to Wednesday', body: 'Confirm or reject this change on your timetable.', target_type: 'insight', target_id: 103, read: false, created_at: '2026-10-19T08:01:00+08:00' },
  { id: 2, kind: 'direct_attention', title: 'Project meeting with Dr Farah', body: 'You were named in CCS2213 Machine Learning – C2.', target_type: 'insight', target_id: 101, read: false, created_at: '2026-10-19T08:13:00+08:00' },
  { id: 3, kind: 'action_required', title: 'Submit HCI usability report', body: 'Due Friday 23 Oct, 23:59.', target_type: 'insight', target_id: 102, read: true, created_at: '2026-10-18T20:05:00+08:00' },
  { id: 4, kind: 'digest', title: 'Your daily digest: 2 new items', body: 'Software engineering internship… · AI hackathon registration open', target_type: 'digest', target_id: 20261018, read: true, created_at: '2026-10-18T19:00:00+08:00' },
  { id: 5, kind: 'important_update', title: 'Mid-semester break dates confirmed', body: 'For all SCI students.', target_type: 'insight', target_id: 104, read: true, created_at: '2026-10-16T10:30:00+08:00' },
]

const sources: Source[] = [
  { id: 1, title: 'CCS2213 Machine Learning – C2', platform: 'whatsapp_group', platform_label: 'WhatsApp group', status: 'active', school: 1, programme: null, intake: null, course: null, section: 1, message_count: 214, added_by_number: false, uniflow_number: '' },
  { id: 2, title: 'CCS2223 HCI – Section C2', platform: 'whatsapp_group', platform_label: 'WhatsApp group', status: 'active', school: 1, programme: null, intake: null, course: null, section: 4, message_count: 87, added_by_number: false, uniflow_number: '' },
  { id: 4, title: 'BCS March 2025 intake', platform: 'whatsapp_group', platform_label: 'WhatsApp group', status: 'pending', school: 1, programme: 10, intake: 100, course: null, section: null, message_count: 0, added_by_number: true, uniflow_number: '+60 12-345 6789' },
  { id: 3, title: 'SCI Student Affairs', platform: 'telegram_channel', platform_label: 'Telegram channel', status: 'disconnected', school: 1, programme: null, intake: null, course: null, section: null, message_count: 42, added_by_number: false, uniflow_number: '' },
]

// --- The handler ---------------------------------------------------------------------------

/** Answers every /api/v1/ call of `page` for the given scenario. Call before page.goto(). */
export async function mockApi(page: Page, scenario: Scenario): Promise<void> {
  const busy = scenario === 'busy' || scenario === 'staff'
  const user = scenario === 'staff' ? staff : student(scenario !== 'new')

  await page.route('**/api/v1/**', async (route: Route) => {
    const request = route.request()
    const url = new URL(request.url())
    const path = url.pathname.replace(/^.*\/api\/v1/, '')
    const method = request.method()
    const json = (body: unknown, status = 200) => route.fulfill({ status, json: body })
    const fail = () => route.fulfill({ status: 500, json: { detail: 'Server error.' } })
    const failing = scenario === 'error'
    const slow = scenario === 'loading'
    const page_ = <T>(results: T[]) => ({ count: results.length, next: null, previous: null, results })

    // Auth
    if (path === '/auth/jwt/refresh/') {
      return scenario === 'visitor' ? json({ detail: 'No refresh token.' }, 401) : json({ access: 'fake-access-token' })
    }
    if (path === '/auth/jwt/create/') return json({ detail: 'No active account found.' }, 401)
    if (path === '/auth/jwt/logout/') return route.fulfill({ status: 204 })
    if (path === '/auth/users/me/') return json(user)
    if (path === '/auth/preferences/choices/') return json(choices)
    if (path.startsWith('/auth/users/')) return route.fulfill({ status: 204 })
    if (path === '/health/') return json({ status: 'ok', db: 'ok' })

    // Reference data
    if (path === '/academics/schools/') return json(schools)
    if (path === '/academics/programmes/') return json(programmes.filter((p) => String(p.school) === (url.searchParams.get('school') ?? String(p.school))))
    if (path === '/academics/intakes/') return json(intakes)

    // Everything below is "my data": the scenario decides.
    if (slow) return // never answered: the page stays in its loading state
    if (method !== 'GET') return json({})

    if (path === '/feed/') return failing ? fail() : json(page_(busy ? feed : []))
    if (path === '/feed/home/') {
      if (failing) return fail()
      const home: Home = {
        direct: busy ? feed.filter((i) => i.tier === 'direct') : [],
        action: busy ? feed.filter((i) => i.tier === 'action') : [],
        important: busy ? feed.filter((i) => i.tier === 'important') : [],
        todays_classes: busy ? slotsFor(0) : [],
        pending_timetable_changes: busy ? changes : [],
        digest_preview: busy ? feed.filter((i) => i.tier === 'digest') : [],
        unread_notifications: busy ? 2 : 0,
      }
      return json(home)
    }
    if (path === '/feed/search/') {
      const q = (url.searchParams.get('q') ?? '').toLowerCase()
      return json(page_(busy ? feed.filter((i) => `${i.title} ${i.summary}`.toLowerCase().includes(q)) : []))
    }
    if (path === '/feed/digest/') {
      return json(busy ? { date: '2026-10-18', items: feed.filter((i) => i.tier === 'digest') } : { date: null, items: [] })
    }
    const feedDetail = path.match(/^\/feed\/(\d+)\/$/)
    if (feedDetail) {
      const found = busy ? feed.find((i) => i.id === Number(feedDetail[1])) : undefined
      return found ? json(detail(found)) : json({ detail: 'Not found.' }, 404)
    }

    if (path === '/notifications/') return failing ? fail() : json(page_(busy ? notifications : []))
    if (path === '/notifications/unread-count/') return json({ count: busy ? 2 : 0 })
    if (path === '/notifications/devices/') return json({ registered: true }, 201)
    if (path === '/notifications/devices/unregister/') return route.fulfill({ status: 204 })
    if (path === '/notifications/push-settings/') {
      return json({ class_changes: true, needs_you: true, daily_digest: false })
    }

    if (path === '/sources/') return failing ? fail() : json(busy ? sources : [])
    // A group UniFlow joined whose WhatsApp name differs from what the student typed.
    if (path === '/sources/4/unclaimed/') return json([{ id: 9, title: 'BCS Mar 2025 – Official', joined_at: '2026-10-19T01:10:00Z' }])

    if (path === '/timetable/my-sections/') return json(busy ? sections : [])
    if (path === '/timetable/semesters/') return json({ current: SEMESTER, next: NEXT_SEMESTER })
    if (path === '/timetable/sections/') {
      const q = (url.searchParams.get('search') ?? url.searchParams.get('q') ?? '').toLowerCase()
      return json(page_(sections.filter((s) => `${s.course.code} ${s.course.name}`.toLowerCase().includes(q))))
    }
    if (path === '/timetable/today/') {
      if (failing) return fail()
      return json({ term: week(busy).term, days: [week(busy).days[0]] })
    }
    if (path === '/timetable/week/') return failing ? fail() : json(week(busy))
    if (path === '/timetable/changes/') return json(busy ? changes : [])
    if (path === '/timetable/imports/') return json([])

    return json({ detail: `No fake answer for ${method} ${path}` }, 404)
  })
}
