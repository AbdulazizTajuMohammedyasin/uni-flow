import { Link, NavLink, Outlet } from 'react-router'

import { useAuth } from '@/context/AuthContext'
import { can } from '@/lib/capabilities'
import { staffNavItems } from '@/lib/navigation'

const linkClass = ({ isActive }: { isActive: boolean }) =>
  [
    'block shrink-0 rounded-lg px-3 py-2 text-sm font-medium whitespace-nowrap',
    isActive ? 'bg-slate-700 text-white' : 'text-slate-300 hover:bg-slate-800 hover:text-white',
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
      <aside className="border-b border-slate-200 bg-slate-900 text-slate-100 md:w-60 md:shrink-0 md:border-r md:border-b-0">
        <div className="flex items-center justify-between px-4 py-3 md:block md:px-6 md:py-5">
          <p className="text-lg font-bold">
            UniFlow <span className="font-medium text-brand-100">Staff</span>
          </p>
          <Link to="/" className="text-sm text-slate-300 hover:text-white md:mt-2 md:block">
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

      <main className="min-w-0 flex-1 px-4 py-6 md:px-8">
        <Outlet />
      </main>
    </div>
  )
}
