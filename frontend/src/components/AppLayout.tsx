import { LayoutDashboard } from 'lucide-react'
import { useEffect } from 'react'
import { Link, NavLink, Outlet } from 'react-router'

import { useAuth } from '@/context/AuthContext'
import { useUnreadCount } from '@/hooks/useNotifications'
import { tellApp } from '@/lib/app'
import { canUseStaffArea } from '@/lib/capabilities'
import { studentNavItems } from '@/lib/navigation'
import { cn } from '@/lib/utils'

import { AccountMenu } from './AccountMenu'
import { HealthBadge } from './HealthBadge'
import { Wordmark } from './Wordmark'
import { SkipLink } from '@/components/SkipLink'

/** Desktop sidebar link: the active page is a lime pill with medium-weight text (not colour
 * alone), plus aria-current="page" from NavLink. */
const sidebarLinkClass = ({ isActive }: { isActive: boolean }) =>
  cn(
    'flex min-h-11 items-center gap-3 rounded-full px-4 text-[0.9375rem] outline-none',
    'focus-visible:ring-3 focus-visible:ring-ring/50',
    isActive
      ? 'bg-sidebar-primary font-medium text-sidebar-primary-foreground focus-visible:ring-foreground focus-visible:ring-offset-2 focus-visible:ring-offset-sidebar'
      : 'font-normal text-sidebar-foreground hover:bg-sidebar-accent',
  )

const bottomLinkClass = ({ isActive }: { isActive: boolean }) =>
  cn(
    'group/tab flex min-h-16 flex-col items-center justify-center gap-1 px-1 text-xs outline-none',
    'focus-visible:ring-3 focus-visible:ring-ring/50 focus-visible:ring-inset',
    isActive ? 'font-medium text-foreground' : 'font-normal text-muted-foreground',
  )

/** Behind the bottom-bar icon: a lime pill on the active page. */
const bottomIconClass = ({ isActive }: { isActive: boolean }) =>
  cn(
    'relative flex h-8 w-14 items-center justify-center rounded-full',
    isActive && 'bg-primary text-primary-foreground',
  )

/** Student-area frame: sidebar on md+ screens; top bar + bottom navigation on phones. */
export default function AppLayout() {
  useTellAppUnread()
  return (
    <div className="min-h-screen md:flex">
      <SkipLink />
      <aside className="hidden md:sticky md:top-0 md:flex md:h-screen md:w-64 md:shrink-0 md:flex-col md:border-r md:border-sidebar-border md:bg-sidebar">
        <Link
          to="/"
          className="mx-3 mt-6 mb-6 w-fit rounded-lg px-3 py-1 text-[1.375rem] text-foreground outline-none focus-visible:ring-3 focus-visible:ring-ring/50"
        >
          <Wordmark />
        </Link>
        <nav aria-label="Sidebar" className="flex flex-col gap-1 px-3">
          {studentNavItems.map((item) => (
            <NavLink key={item.to} to={item.to} end={item.end} className={sidebarLinkClass}>
              <item.icon aria-hidden className="size-[1.125rem] shrink-0" />
              {item.label}
              {item.badge && <UnreadBadge className="ml-auto" />}
            </NavLink>
          ))}
          <StaffDashboardLink />
        </nav>
        <div className="mt-auto space-y-2 border-t border-sidebar-border p-3">
          {import.meta.env.DEV && (
            <div className="px-2">
              <HealthBadge />
            </div>
          )}
          <AccountMenu variant="full" />
        </div>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-20 flex h-14 items-center justify-between border-b border-border bg-background/95 px-4 backdrop-blur-sm md:hidden">
          <Link to="/" className="text-lg text-foreground">
            <Wordmark />
          </Link>
          <div className="flex items-center gap-1">
            {import.meta.env.DEV && <HealthBadge />}
            <AccountMenu variant="compact" />
          </div>
        </header>

        {/* Bottom padding on phones keeps content clear of the bottom bar. */}
        <main id="main" tabIndex={-1} className="flex-1 scroll-mt-16 px-4 pt-5 pb-28 outline-none md:px-10 md:pt-10 md:pb-12">
          <div className="mx-auto w-full max-w-5xl">
            <Outlet />
          </div>
        </main>
      </div>

      <nav
        aria-label="Bottom navigation"
        className="fixed inset-x-0 bottom-0 z-20 grid grid-cols-5 border-t border-border bg-background/95 pb-[env(safe-area-inset-bottom)] backdrop-blur-sm md:hidden"
      >
        {studentNavItems.map((item) => (
          <NavLink key={item.to} to={item.to} end={item.end} className={bottomLinkClass}>
            {({ isActive }) => (
              <>
                <span className={bottomIconClass({ isActive })}>
                  <item.icon aria-hidden className="size-5" />
                  {item.badge && <UnreadBadge className="absolute -top-1 right-1" />}
                </span>
                {item.shortLabel}
              </>
            )}
          </NavLink>
        ))}
      </nav>
    </div>
  )
}

/** Inside the phone app: the unread count, so the app icon shows the same number as the bell. */
function useTellAppUnread() {
  const count = useUnreadCount().data
  useEffect(() => {
    if (count !== undefined) tellApp({ type: 'unread', count })
  }, [count])
}

/** The number of unread alerts (checked every minute while the tab is visible). */
function UnreadBadge({ className }: { className?: string }) {
  const unread = useUnreadCount()
  const count = unread.data ?? 0
  if (count === 0) return null
  return (
    <span
      aria-label={`${count} unread`}
      className={cn(
        'inline-flex h-5 min-w-5 items-center justify-center rounded-full bg-destructive px-1.5 text-xs font-medium text-destructive-foreground tabular-nums',
        className,
      )}
    >
      {count > 99 ? '99+' : count}
    </span>
  )
}

/** Link to the staff dashboard, shown only to users who can use it. */
function StaffDashboardLink() {
  const { user } = useAuth()
  if (!canUseStaffArea(user)) {
    return null
  }
  return (
    <Link
      to="/staff"
      className="mt-3 flex min-h-11 items-center gap-3 rounded-full px-4 text-[0.9375rem] text-sidebar-foreground outline-none hover:bg-sidebar-accent focus-visible:ring-3 focus-visible:ring-ring/50"
    >
      <LayoutDashboard aria-hidden className="size-[1.125rem] shrink-0" />
      Staff dashboard
    </Link>
  )
}
