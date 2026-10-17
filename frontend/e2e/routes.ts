import type { Scenario } from './mock-api'

/** One page in one state, as captured by the screenshots and checked by the smoke tests. */
export type Screen = {
  name: string // file name, e.g. "for-you--busy"
  path: string
  scenario: Scenario
  /** Text that proves the page has finished loading (Playwright waits for it). */
  ready: string | RegExp
  /** Something to do before the screenshot, e.g. open the account menu. */
  action?: 'open-account-menu'
}

export const screens: Screen[] = [
  // Not logged in
  { name: 'login', path: '/login', scenario: 'visitor', ready: 'Log in' },
  { name: 'register', path: '/register', scenario: 'visitor', ready: 'Create your account' },
  { name: 'forgot-password', path: '/forgot-password', scenario: 'visitor', ready: /password/i },
  { name: 'reset-password', path: '/reset-password/MQ/set-password-token', scenario: 'visitor', ready: /password/i },
  { name: 'privacy', path: '/privacy', scenario: 'visitor', ready: /privacy/i },
  { name: 'not-found', path: '/no-such-page', scenario: 'visitor', ready: 'Page not found' },

  // A busy student
  { name: 'for-you--busy', path: '/', scenario: 'busy', ready: 'Project meeting with Dr Farah' },
  { name: 'insight--busy', path: '/insights/101', scenario: 'busy', ready: 'Where it came from' },
  { name: 'insight-change--busy', path: '/insights/103', scenario: 'busy', ready: 'Where it came from' },
  { name: 'digest--busy', path: '/digest', scenario: 'busy', ready: 'AI hackathon registration open' },
  { name: 'timetable-today--busy', path: '/timetable', scenario: 'busy', ready: 'My sections' },
  { name: 'timetable-week--busy', path: '/timetable?view=week', scenario: 'busy', ready: 'Next week' },
  { name: 'groups--busy', path: '/sources', scenario: 'busy', ready: 'SCI Student Affairs' },
  { name: 'search--busy', path: '/search?q=internship', scenario: 'busy', ready: /internship at a Kuala Lumpur/ },
  { name: 'notifications--busy', path: '/notifications', scenario: 'busy', ready: 'Mark all as read' },
  { name: 'profile--busy', path: '/profile', scenario: 'busy', ready: 'Your studies' },
  { name: 'account-menu--busy', path: '/', scenario: 'busy', ready: 'Project meeting with Dr Farah', action: 'open-account-menu' },

  // Nothing yet
  { name: 'for-you--empty', path: '/', scenario: 'empty', ready: 'Nothing for you yet' },
  { name: 'timetable--empty', path: '/timetable', scenario: 'empty', ready: "You haven't added your classes yet" },
  { name: 'groups--empty', path: '/sources', scenario: 'empty', ready: 'No groups yet' },
  { name: 'search--empty', path: '/search?q=scholarship', scenario: 'empty', ready: 'Nothing found' },
  { name: 'notifications--empty', path: '/notifications', scenario: 'empty', ready: 'No notifications yet' },
  { name: 'digest--empty', path: '/digest', scenario: 'empty', ready: 'Nothing in this digest' },

  // Failures and waiting
  { name: 'for-you--error', path: '/', scenario: 'error', ready: 'Could not load your feed' },
  { name: 'notifications--error', path: '/notifications', scenario: 'error', ready: 'Could not load your notifications' },
  { name: 'for-you--loading', path: '/', scenario: 'loading', ready: 'Only the information that matters to you' },

  // Other roles and steps
  { name: 'onboarding--new', path: '/onboarding', scenario: 'new', ready: /Welcome, Aisha/ },
  { name: 'staff--staff', path: '/staff', scenario: 'staff', ready: 'Staff dashboard' },
]

export const viewports = {
  phone: { width: 390, height: 844 },
  desktop: { width: 1440, height: 1000 },
}

/** Widths the smoke tests check for sideways scrolling. */
export const smokeWidths = [360, 390, 768, 1024, 1440]
