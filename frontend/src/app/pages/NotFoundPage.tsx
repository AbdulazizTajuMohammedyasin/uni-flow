import { Link } from 'react-router'

/** Shown for any address that does not match a route. */
export function NotFoundPage() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center px-4 text-center">
      <p className="text-sm font-semibold text-brand-600">404</p>
      <h1 className="mt-2 text-3xl font-bold tracking-tight">Page not found</h1>
      <p className="mt-2 text-slate-600">The page you are looking for does not exist.</p>
      <Link
        to="/"
        className="mt-6 rounded-lg bg-brand-600 px-4 py-2 font-medium text-white hover:bg-brand-700"
      >
        Go to home
      </Link>
    </main>
  )
}
