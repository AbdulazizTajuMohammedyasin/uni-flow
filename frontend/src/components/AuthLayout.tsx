import { CalendarCheck, Inbox, MessagesSquare, type LucideIcon } from 'lucide-react'
import { Link, Outlet, useMatches } from 'react-router'

import { Wordmark } from './Wordmark'

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

const focusRing = 'rounded-sm outline-none focus-visible:ring-3 focus-visible:ring-ring'

/** Frame for the public pages and onboarding (no app navigation).
 * Computers: a panel saying what UniFlow is on the left (the page colour fading into a soft blue wash),
 * the form on the right. Phones: the same wash as a band above the form. Long text (the privacy notice)
 * gets one readable column instead. */
export default function AuthLayout() {
  if (useReadingFrame()) {
    return (
      <main className="min-h-screen px-4 py-10 sm:py-14">
        <div className="mx-auto max-w-[68ch]">
          <Link to="/" className="text-xl text-foreground">
            <Wordmark />
          </Link>
          <div className="mt-6 rounded-2xl bg-card p-6 shadow-card sm:p-10">
            <Outlet />
          </div>
        </div>
      </main>
    )
  }

  return (
    <main className="min-h-screen lg:grid lg:grid-cols-2">
      <aside className="hero-wash hidden flex-col border-r border-border px-12 py-11 lg:flex xl:px-14">
        <Wordmark className="text-2xl" />
        <div className="mt-auto max-w-xl space-y-10 py-10">
          <div className="space-y-5">
            <p className="text-[0.9375rem] text-muted-foreground">For Albukhary International University students</p>
            {/* Not a heading: the page's own h1 (e.g. "Log in") comes first for screen readers. */}
            <p className="text-[3.5rem] leading-[0.98] font-semibold tracking-[-0.035em] text-balance xl:text-[4.5rem]">
              Only the information that matters to you.
            </p>
          </div>
          <ul className="max-w-lg space-y-4">
            {POINTS.map(({ icon: Icon, text }) => (
              <li key={text} className="flex gap-3.5">
                <span className="flex size-9 shrink-0 items-center justify-center rounded-full bg-card text-link shadow-card">
                  <Icon aria-hidden className="size-4" />
                </span>
                <p className="pt-1.5 text-base leading-relaxed">{text}</p>
              </li>
            ))}
          </ul>
        </div>
        <p className="mt-auto text-sm">
          How UniFlow uses information:{' '}
          <Link to="/privacy" className={`font-medium text-island-accent underline underline-offset-4 hover:decoration-2 ${focusRing}`}>
            Privacy notice
          </Link>
        </p>
      </aside>

      <div className="flex min-h-screen flex-col">
        <div className="hero-wash rounded-b-[1.75rem] border-b border-border px-5 pt-5 pb-7 lg:hidden">
          <Link to="/" className={`inline-block text-xl ${focusRing}`}>
            <Wordmark />
          </Link>
          <p className="mt-6 text-[2rem] leading-[1.02] font-semibold tracking-[-0.03em] text-balance">
            Only the information that matters to you.
          </p>
          <p className="mt-2 text-sm text-muted-foreground">For Albukhary International University students.</p>
        </div>
        <div className="flex flex-1 flex-col items-center px-4 py-6 lg:justify-center lg:py-10">
          <div className="w-full max-w-md rounded-2xl bg-card p-6 shadow-card sm:p-8 lg:p-10">
            <Outlet />
          </div>
        </div>
      </div>
    </main>
  )
}
