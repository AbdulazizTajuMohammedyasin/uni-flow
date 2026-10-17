import { Bell, CalendarDays, Inbox, MessagesSquare, Search, type LucideIcon } from 'lucide-react'

import type { Capability } from '@/types/auth'

/** Student-area navigation, shared by the desktop sidebar and the mobile bottom bar. */
export type NavItem = {
  to: string
  label: string
  /** Shorter label for the narrow mobile bottom bar. */
  shortLabel: string
  icon: LucideIcon
  /** Match the path exactly (only needed for "/"). */
  end?: boolean
  /** Show the number of unread alerts next to it. */
  badge?: 'unread'
}

export const studentNavItems: NavItem[] = [
  { to: '/', label: 'For you', shortLabel: 'For you', icon: Inbox, end: true },
  { to: '/timetable', label: 'Timetable', shortLabel: 'Classes', icon: CalendarDays },
  { to: '/sources', label: 'Groups', shortLabel: 'Groups', icon: MessagesSquare },
  { to: '/search', label: 'Search', shortLabel: 'Search', icon: Search },
  { to: '/notifications', label: 'Notifications', shortLabel: 'Alerts', icon: Bell, badge: 'unread' },
]

/** Staff-dashboard navigation. Each item shows only if the user has its capability. */
export type StaffNavItem = {
  to: string
  label: string
  /** Leave out for items every staff user sees (the staff home). */
  cap?: Capability
  end?: boolean
}

export const staffNavItems: StaffNavItem[] = [
  { to: '/staff', label: 'Overview', end: true },
  { to: '/staff/announcements', label: 'Announcements', cap: 'announcements.manage' },
  { to: '/staff/events', label: 'Events', cap: 'events.manage' },
  { to: '/staff/documents', label: 'Documents', cap: 'documents.manage' },
  { to: '/staff/applications', label: 'Applications', cap: 'applications.manage' },
  { to: '/staff/communities', label: 'Communities', cap: 'communities.manage' },
  { to: '/staff/timetable', label: 'Timetable', cap: 'timetable.manage' },
  { to: '/staff/academics', label: 'Schools & programmes', cap: 'academics.manage' },
  { to: '/staff/users', label: 'Users', cap: 'users.manage' },
]
