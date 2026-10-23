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

/** Focus on the lime panel: an ink ring in both themes (the dark theme's lime ring would vanish). */
const onLimeFocus = 'rounded-sm outline-none focus-visible:ring-3 focus-visible:ring-primary-foreground'

/** Frame for the public pages and onboarding (no app navigation).
 * Computers: a lime panel saying what UniFlow is on the left, the form on the right. Phones: a lime
 * band above the form. Long text (the privacy notice) gets one readable column instead. */
export default function AuthLayout() {
  if (useReadingFrame()) {
    return (
      <main className="min-h-screen px-4 py-10 sm:py-14">
        <div className="mx-auto max-w-[68ch]">
          <Link to="/" className="text-xl text-foreground">
            <Wordmark />
          </Link>
          <div className="mt-6 rounded-2xl bg-card p-6 ring-1 ring-border sm:p-10">
            <Outlet />
          </div>
        </div>
      </main>
    )
  }

  return (
    <main className="min-h-screen lg:grid lg:grid-cols-2">
      <aside className="hidden flex-col bg-primary px-12 py-11 text-primary-foreground lg:flex xl:px-14">
        <Wordmark inverted className="text-2xl" />
        <div className="mt-auto max-w-xl space-y-10 py-10">
          <div className="space-y-5">
            <p className="text-[0.9375rem]">For Albukhary International University students</p>
            {/* Not a heading: the page's own h1 (e.g. "Log in") comes first for screen readers. */}
            <p className="text-[3.5rem] leading-[0.98] font-medium tracking-[-0.035em] text-balance xl:text-[4.5rem]">
              Only the information that matters to you.
            </p>
          </div>
          <ul className="max-w-lg space-y-4">
            {POINTS.map(({ icon: Icon, text }) => (
              <li key={text} className="flex gap-3.5">
                <span className="flex size-9 shrink-0 items-center justify-center rounded-full border-[1.5px] border-primary-foreground">
                  <Icon aria-hidden className="size-4" />
                </span>
                <p className="pt-1.5 text-base leading-relaxed">{text}</p>
              </li>
            ))}
          </ul>
        </div>
        <p className="mt-auto text-sm">
          How UniFlow uses information:{' '}
          <Link to="/privacy" className={`font-medium underline underline-offset-4 hover:decoration-2 ${onLimeFocus}`}>
            Privacy notice
          </Link>
        </p>
      </aside>

      <div className="flex min-h-screen flex-col">
        <div className="rounded-b-[1.75rem] bg-primary px-5 pt-5 pb-7 text-primary-foreground lg:hidden">
          <Link to="/" className={`inline-block text-xl ${onLimeFocus}`}>
            <Wordmark inverted />
          </Link>
          <p className="mt-6 text-[2rem] leading-[1.02] font-medium tracking-[-0.03em] text-balance">
            Only the information that matters to you.
          </p>
          <p className="mt-2 text-sm">For Albukhary International University students.</p>
        </div>
        <div className="flex flex-1 flex-col items-center px-4 py-6 lg:justify-center lg:py-10">
          <div className="w-full max-w-md rounded-2xl bg-card p-6 ring-1 ring-border sm:p-8 lg:p-10">
            <Outlet />
          </div>
        </div>
      </div>
    </main>
  )
}
