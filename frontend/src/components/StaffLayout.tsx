import { Link, Outlet } from 'react-router'

/**
 * Staff-dashboard frame. Its menu is intentionally empty for now: from M2.8 the items
 * are built from the logged-in user's capabilities (the backend still enforces access).
 */
export default function StaffLayout() {
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
        <nav aria-label="Staff" className="hidden px-6 pb-6 text-sm text-slate-400 md:block">
          Menu items appear here based on your permissions.
        </nav>
      </aside>

      <main className="min-w-0 flex-1 px-4 py-6 md:px-8">
        <Outlet />
      </main>
    </div>
  )
}
