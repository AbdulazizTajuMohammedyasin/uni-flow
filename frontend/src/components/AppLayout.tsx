import { LayoutDashboard } from 'lucide-react'
import { Link, NavLink, Outlet } from 'react-router'

import { useAuth } from '@/context/AuthContext'
import { useUnreadCount } from '@/hooks/useNotifications'
import { canUseStaffArea } from '@/lib/capabilities'
import { studentNavItems } from '@/lib/navigation'
import { cn } from '@/lib/utils'

import { AccountMenu } from './AccountMenu'
import { HealthBadge } from './HealthBadge'

/** Desktop sidebar link: the active page gets a tinted background, a bar and bold text
 * (not colour alone), plus aria-current="page" from NavLink. */
const sidebarLinkClass = ({ isActive }: { isActive: boolean }) =>
  cn(
    'relative flex min-h-10 items-center gap-3 rounded-lg px-3 text-sm outline-none',
    'focus-visible:ring-3 focus-visible:ring-ring/50',
    isActive
      ? 'bg-sidebar-accent font-semibold text-sidebar-accent-foreground before:absolute before:inset-y-2 before:left-0 before:w-1 before:rounded-full before:bg-primary'
      : 'font-medium text-sidebar-foreground hover:bg-muted',
  )

const bottomLinkClass = ({ isActive }: { isActive: boolean }) =>
  cn(
    'flex min-h-14 flex-col items-center justify-center gap-0.5 px-1 text-xs outline-none',
    'focus-visible:ring-3 focus-visible:ring-ring/50 focus-visible:ring-inset',
    isActive ? 'font-semibold text-primary' : 'font-medium text-muted-foreground',
  )

/** Student-area frame: sidebar on md+ screens; top bar + bottom navigation on phones. */
export default function AppLayout() {
  return (
    <div className="min-h-screen md:flex">
      <aside className="hidden md:sticky md:top-0 md:flex md:h-screen md:w-64 md:shrink-0 md:flex-col md:border-r md:border-sidebar-border md:bg-sidebar">
        <Link
          to="/"
          className="mx-3 mt-5 mb-4 rounded-lg px-3 py-1 text-xl font-bold tracking-tight text-primary outline-none focus-visible:ring-3 focus-visible:ring-ring/50"
        >
          UniFlow
        </Link>
        <nav aria-label="Sidebar" className="flex flex-col gap-0.5 px-3">
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
        <header className="sticky top-0 z-20 flex h-14 items-center justify-between border-b border-border bg-card px-4 md:hidden">
          <Link to="/" className="text-lg font-bold tracking-tight text-primary">
            UniFlow
          </Link>
          <div className="flex items-center gap-1">
            {import.meta.env.DEV && <HealthBadge />}
            <AccountMenu variant="compact" />
          </div>
        </header>

        {/* Bottom padding on phones keeps content clear of the bottom bar. */}
        <main className="flex-1 px-4 pt-5 pb-28 md:px-10 md:pt-10 md:pb-12">
          <div className="mx-auto w-full max-w-5xl">
            <Outlet />
          </div>
        </main>
      </div>

      <nav
        aria-label="Bottom navigation"
        className="fixed inset-x-0 bottom-0 z-20 grid grid-cols-5 border-t border-border bg-card pb-[env(safe-area-inset-bottom)] md:hidden"
      >
        {studentNavItems.map((item) => (
          <NavLink key={item.to} to={item.to} end={item.end} className={bottomLinkClass}>
            <span className="relative">
              <item.icon aria-hidden className="size-5" />
              {item.badge && <UnreadBadge className="absolute -top-1.5 left-3" />}
            </span>
            {item.shortLabel}
          </NavLink>
        ))}
      </nav>
    </div>
  )
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
        'inline-flex h-5 min-w-5 items-center justify-center rounded-full bg-destructive px-1.5 text-xs font-semibold text-destructive-foreground tabular-nums',
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
      className="mt-3 flex min-h-10 items-center gap-3 rounded-lg px-3 text-sm font-medium text-sidebar-foreground outline-none hover:bg-muted focus-visible:ring-3 focus-visible:ring-ring/50"
    >
      <LayoutDashboard aria-hidden className="size-[1.125rem] shrink-0" />
      Staff dashboard
    </Link>
  )
}
