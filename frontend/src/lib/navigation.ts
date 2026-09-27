/** Student-area navigation, shared by the desktop sidebar and the mobile bottom bar. */
export type NavItem = {
  to: string
  label: string
  /** Shorter label for the narrow mobile bottom bar. */
  shortLabel: string
  /** Match the path exactly (only needed for "/"). */
  end?: boolean
}

export const studentNavItems: NavItem[] = [
  { to: '/', label: 'Home', shortLabel: 'Home', end: true },
  { to: '/announcements', label: 'Announcements', shortLabel: 'News' },
  { to: '/events', label: 'Events', shortLabel: 'Events' },
  { to: '/timetable', label: 'Timetable', shortLabel: 'Classes' },
  { to: '/communities', label: 'Communities', shortLabel: 'Groups' },
]
