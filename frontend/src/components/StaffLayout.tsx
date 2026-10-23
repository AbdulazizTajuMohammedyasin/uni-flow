import { Link, NavLink, Outlet } from 'react-router'

import { useAuth } from '@/context/AuthContext'
import { can } from '@/lib/capabilities'
import { staffNavItems } from '@/lib/navigation'
import { SkipLink } from '@/components/SkipLink'
import { Wordmark } from '@/components/Wordmark'

const linkClass = ({ isActive }: { isActive: boolean }) =>
  [
    'block shrink-0 rounded-full px-4 py-2 text-sm whitespace-nowrap',
    isActive
      ? 'bg-sidebar-primary font-medium text-sidebar-primary-foreground'
      : 'font-normal text-sidebar-foreground hover:bg-sidebar-accent',
  ].join(' ')

/**
 * Staff-dashboard frame. The menu shows only the sections this user may manage
 * (the backend still checks every action). On phones the menu scrolls sideways.
 */
export default function StaffLayout() {
  const { user } = useAuth()
  const items = staffNavItems.filter((item) => !item.cap || can(user, item.cap))

  return (
    <div className="min-h-screen md:flex">
      <SkipLink />
      <aside className="border-b border-border bg-sidebar text-sidebar-foreground md:w-60 md:shrink-0 md:border-r md:border-b-0">
        <div className="flex items-center justify-between px-4 py-3 md:block md:px-6 md:py-5">
          <p className="flex items-center gap-2 text-lg">
            <Wordmark /> <span className="font-normal text-muted-foreground">Staff</span>
          </p>
          <Link to="/" className="text-sm text-muted-foreground hover:text-foreground md:mt-2 md:block">
            ← Back to UniFlow
          </Link>
        </div>
        <nav
          aria-label="Staff"
          className="flex gap-1 overflow-x-auto px-3 pb-3 md:flex-col md:overflow-visible md:pb-6"
        >
          {items.map((item) => (
            <NavLink key={item.to} to={item.to} end={item.end} className={linkClass}>
              {item.label}
            </NavLink>
          ))}
        </nav>
      </aside>

      <main id="main" tabIndex={-1} className="min-w-0 flex-1 px-4 py-6 outline-none md:px-8">
        <Outlet />
      </main>
    </div>
  )
}
