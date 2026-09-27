import { Outlet } from 'react-router'

/** Frame for login/registration pages: centred card, no navigation. */
export default function AuthLayout() {
  return (
    <main className="flex min-h-screen items-center justify-center px-4 py-10">
      <div className="w-full max-w-md">
        <p className="mb-6 text-center text-2xl font-bold text-brand-600">UniFlow</p>
        <div className="rounded-2xl bg-white p-6 shadow-sm ring-1 ring-slate-200 sm:p-8">
          <Outlet />
        </div>
      </div>
    </main>
  )
}
