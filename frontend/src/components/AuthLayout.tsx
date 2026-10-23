import { CalendarCheck, Inbox, MessagesSquare, type LucideIcon } from 'lucide-react'
import { Link, Outlet, useMatches } from 'react-router'

/** What UniFlow really does, in three lines (shown next to the forms on computers). */
const POINTS: { icon: LucideIcon; text: string }[] = [
  { icon: MessagesSquare, text: "Reads the academic WhatsApp and Telegram groups you add, so you don't have to scroll them." },
  { icon: Inbox, text: "Puts first what needs you: when you're named, deadlines, and things to do." },
  { icon: CalendarCheck, text: 'Keeps your timetable in one place. A class change only applies when you confirm it.' },
]

/** A route can ask for the wide reading frame (the privacy notice) with `handle: { frame: 'reading' }`. */
function useReadingFrame(): boolean {
  return useMatches().some((match) => (match.handle as { frame?: string } | undefined)?.frame === 'reading')
}

/** Frame for the public pages and onboarding (no app navigation).
 * Computers: what UniFlow is on the left, the form on the right. Phones: one column.
 * Long text (the privacy notice) gets one readable column instead. */
export default function AuthLayout() {
  if (useReadingFrame()) {
    return (
      <main className="min-h-screen px-4 py-10 sm:py-14">
        <div className="mx-auto max-w-[68ch]">
          <Link to="/" className="text-xl font-medium text-foreground">
            UniFlow
          </Link>
          <div className="mt-6 rounded-xl bg-card p-6 ring-1 ring-border sm:p-10">
            <Outlet />
          </div>
        </div>
      </main>
    )
  }

  return (
    <main className="min-h-screen lg:grid lg:grid-cols-[minmax(0,5fr)_minmax(0,7fr)]">
      <aside className="hidden flex-col justify-between border-r border-border bg-sidebar px-12 py-12 lg:flex">
        <p className="text-2xl font-medium text-foreground">UniFlow</p>
        <div className="max-w-md space-y-8">
          <div className="space-y-3">
            <p className="text-sm font-medium text-foreground">For Albukhary International University students</p>
            {/* Not a heading: the page's own h1 (e.g. "Log in") comes first for screen readers. */}
            <p className="text-3xl leading-tight font-medium tracking-tight text-balance">
              Only the information that matters to you.
            </p>
          </div>
          <ul className="space-y-5">
            {POINTS.map(({ icon: Icon, text }) => (
              <li key={text} className="flex gap-3">
                <span className="flex size-9 shrink-0 items-center justify-center rounded-full bg-primary/25 text-foreground">
                  <Icon aria-hidden className="size-4" />
                </span>
                <p className="pt-1.5 text-[0.9375rem] leading-relaxed text-muted-foreground">{text}</p>
              </li>
            ))}
          </ul>
        </div>
        <p className="text-sm text-muted-foreground">
          How UniFlow uses information:{' '}
          <Link to="/privacy" className="font-medium text-foreground underline underline-offset-4 hover:decoration-2">
            Privacy notice
          </Link>
        </p>
      </aside>

      <div className="flex min-h-screen flex-col items-center justify-center px-4 py-10">
        <div className="w-full max-w-md">
          <div className="mb-6 text-center lg:hidden">
            <p className="text-2xl font-medium text-foreground">UniFlow</p>
            <p className="mt-1 text-sm text-muted-foreground">Only the information that matters to you.</p>
          </div>
          <div className="rounded-xl bg-card p-6 ring-1 ring-border sm:p-8">
            <Outlet />
          </div>
        </div>
      </div>
    </main>
  )
}
