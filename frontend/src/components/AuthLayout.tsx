import { Outlet } from 'react-router'

/** Frame for login/registration pages: centred card, no navigation. */
export default function AuthLayout() {
  return (
    <main className="flex min-h-screen items-center justify-center px-4 py-10">
      <div className="w-full max-w-md">
        <p className="mb-6 text-center text-2xl font-bold text-primary">UniFlow</p>
        <div className="rounded-2xl bg-card p-6 shadow-sm ring-1 ring-border sm:p-8">
          <Outlet />
        </div>
      </div>
    </main>
  )
}
