import { Link } from 'react-router'

import { Button } from '@/components/ui/button'

/** Shown when a logged-in user opens a page they are not allowed to use (403). */
export function NoAccessPage() {
  return (
    <section className="mx-auto flex max-w-md flex-col items-center px-4 py-24 text-center">
      <p className="text-sm font-semibold text-brand-600">403</p>
      <h1 className="mt-2 text-3xl font-bold tracking-tight">No access</h1>
      <p className="mt-2 text-slate-600">
        Your account is not allowed to use this page. If you think this is a mistake, contact a
        UniFlow administrator.
      </p>
      <Button asChild size="lg" className="mt-6">
        <Link to="/">Go to home</Link>
      </Button>
    </section>
  )
}
