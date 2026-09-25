import { NavLink, Outlet } from 'react-router'

import { studentNavItems } from '../navigation'

const sidebarLinkClass = ({ isActive }: { isActive: boolean }) =>
  [
    'block rounded-lg px-3 py-2 text-sm font-medium',
    isActive ? 'bg-brand-50 text-brand-700' : 'text-slate-700 hover:bg-slate-100',
  ].join(' ')

const bottomLinkClass = ({ isActive }: { isActive: boolean }) =>
  [
    'flex min-h-11 flex-col items-center justify-center px-1 text-xs font-medium',
    isActive ? 'text-brand-700' : 'text-slate-600',
  ].join(' ')

/** Student-area frame: sidebar on md+ screens, top bar + bottom navigation on phones. */
export default function AppLayout() {
  return (
    <div className="min-h-screen md:flex">
      <aside className="hidden md:flex md:w-60 md:shrink-0 md:flex-col md:border-r md:border-slate-200 md:bg-white">
        <div className="px-6 py-5 text-xl font-bold text-brand-600">UniFlow</div>
        <nav aria-label="Sidebar" className="flex flex-col gap-1 px-3">
          {studentNavItems.map((item) => (
            <NavLink key={item.to} to={item.to} end={item.end} className={sidebarLinkClass}>
              {item.label}
            </NavLink>
          ))}
        </nav>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-10 border-b border-slate-200 bg-white px-4 py-3 md:hidden">
          <span className="text-lg font-bold text-brand-600">UniFlow</span>
        </header>

        {/* Extra bottom padding on phones so content is not hidden behind the bottom bar. */}
        <main className="flex-1 px-4 pt-6 pb-24 md:px-8 md:pb-8">
          <Outlet />
        </main>
      </div>

      <nav
        aria-label="Bottom navigation"
        className="fixed inset-x-0 bottom-0 z-10 grid grid-cols-5 border-t border-slate-200 bg-white md:hidden"
      >
        {studentNavItems.map((item) => (
          <NavLink key={item.to} to={item.to} end={item.end} className={bottomLinkClass}>
            {item.shortLabel}
          </NavLink>
        ))}
      </nav>
    </div>
  )
}
