import { Link, NavLink, Outlet, useNavigate } from 'react-router'

import { Button } from '@/components/ui/button'
import { useAuth } from '@/context/AuthContext'
import { useUnreadCount } from '@/hooks/useNotifications'

import { canUseStaffArea } from '@/lib/capabilities'
import { studentNavItems } from '@/lib/navigation'

import { HealthBadge } from './HealthBadge'

const sidebarLinkClass = ({ isActive }: { isActive: boolean }) =>
  [
    'block rounded-lg px-3 py-2 text-sm font-medium',
    isActive ? 'bg-accent text-accent-foreground' : 'text-foreground hover:bg-muted',
  ].join(' ')

const bottomLinkClass = ({ isActive }: { isActive: boolean }) =>
  [
    'flex min-h-11 flex-col items-center justify-center px-1 text-xs font-medium',
    isActive ? 'text-primary' : 'text-muted-foreground',
  ].join(' ')

/** Student-area frame: sidebar on md+ screens, top bar + bottom navigation on phones. */
export default function AppLayout() {
  return (
    <div className="min-h-screen md:flex">
      <aside className="hidden md:flex md:w-60 md:shrink-0 md:flex-col md:border-r md:border-border md:bg-sidebar">
        <div className="px-6 py-5 text-xl font-bold text-primary">UniFlow</div>
        <nav aria-label="Sidebar" className="flex flex-col gap-1 px-3">
          {studentNavItems.map((item) => (
            <NavLink key={item.to} to={item.to} end={item.end} className={sidebarLinkClass}>
              {item.label}
              {item.badge && <UnreadBadge />}
            </NavLink>
          ))}
          <StaffDashboardLink className="mt-4 block rounded-lg px-3 py-2 text-sm font-medium text-foreground hover:bg-muted" />
        </nav>
        <div className="mt-auto space-y-3 px-6 py-4">
          {import.meta.env.DEV && <HealthBadge />}
          <UserMenu />
        </div>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-10 flex items-center justify-between border-b border-border bg-card px-4 py-3 md:hidden">
          <span className="text-lg font-bold text-primary">UniFlow</span>
          <div className="flex items-center gap-3">
            {import.meta.env.DEV && <HealthBadge />}
            <StaffDashboardLink className="text-sm font-medium text-primary" />
            <Link to="/profile" className="text-sm font-medium text-primary">
              Profile
            </Link>
          </div>
        </header>

        {/* Extra bottom padding on phones so content is not hidden behind the bottom bar. */}
        <main className="flex-1 px-4 pt-6 pb-24 md:px-8 md:pb-8">
          <Outlet />
        </main>
      </div>

      <nav
        aria-label="Bottom navigation"
        className="fixed inset-x-0 bottom-0 z-10 grid grid-cols-5 border-t border-border bg-card md:hidden"
      >
        {studentNavItems.map((item) => (
          <NavLink key={item.to} to={item.to} end={item.end} className={bottomLinkClass}>
            <span>
              {item.shortLabel}
              {item.badge && <UnreadBadge />}
            </span>
          </NavLink>
        ))}
      </nav>
    </div>
  )
}

/** The red number of unread alerts (checked every minute while the tab is visible). */
function UnreadBadge() {
  const unread = useUnreadCount()
  const count = unread.data ?? 0
  if (count === 0) return null
  return (
    <span
      aria-label={`${count} unread`}
      className="ml-2 inline-flex min-w-5 items-center justify-center rounded-full bg-destructive px-1.5 text-xs font-semibold text-destructive-foreground"
    >
      {count > 99 ? '99+' : count}
    </span>
  )
}

/** Sidebar footer: who is logged in, a link to the profile page, and log out. */
function UserMenu() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  async function handleLogout() {
    await logout()
    navigate('/login', { replace: true })
  }

  return (
    <div className="border-t border-border pt-3">
      <p className="truncate text-sm font-medium">{user?.full_name}</p>
      <div className="mt-2 flex gap-2">
        <Button asChild size="sm" variant="outline">
          <NavLink to="/profile">Profile</NavLink>
        </Button>
        <Button size="sm" variant="ghost" onClick={handleLogout}>
          Log out
        </Button>
      </div>
    </div>
  )
}

/** Link to the staff dashboard, shown only to users who can use it. */
function StaffDashboardLink({ className }: { className: string }) {
  const { user } = useAuth()
  if (!canUseStaffArea(user)) {
    return null
  }
  return (
    <Link to="/staff" className={className}>
      Staff dashboard
    </Link>
  )
}
