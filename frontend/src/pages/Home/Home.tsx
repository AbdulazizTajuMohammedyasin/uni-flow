import { ArrowUpRight, Check, CircleDot, X, type LucideIcon } from 'lucide-react'
import { Link } from 'react-router'

import { Button } from '@/components/ui/button'
import { Wordmark } from '@/components/Wordmark'
import { cn } from '@/lib/utils'

// Screenshots of the real app with made-up data (e2e/mock-api.ts), made by `npm run screens:readme`.
import announcement from '@/assets/home/announcement.png'
import forYou from '@/assets/home/for-you.png'
import notifications from '@/assets/home/notifications.png'
import phoneAnnouncement from '@/assets/home/phone-announcement.png'
import phoneForYou from '@/assets/home/phone-for-you.png'
import phoneNotifications from '@/assets/home/phone-notifications.png'
import phoneSearch from '@/assets/home/phone-search.png'
import phoneTimetable from '@/assets/home/phone-timetable.png'
import search from '@/assets/home/search.png'
import timetableWeek from '@/assets/home/timetable-week.png'

/** Focus on the lime bands: an ink ring in both themes (a lime ring would vanish). */
const onLimeFocus = 'outline-none focus-visible:ring-3 focus-visible:ring-primary-foreground focus-visible:ring-offset-2 focus-visible:ring-offset-primary'
/** Buttons on the lime bands: ink with lime text, and an ink outline. */
const inkButton = cn('bg-primary-foreground text-primary hover:bg-primary-foreground/85', onLimeFocus)
const inkOutline = cn('border-primary-foreground bg-transparent text-primary-foreground hover:bg-primary-foreground/10', onLimeFocus)

const PROBLEMS = [
  { title: 'Class changes scroll away', text: 'A room change is posted once, then lost under the replies.' },
  { title: 'Deadlines are mentioned in passing', text: 'A due date hides in the middle of a long message.' },
  { title: 'Messages for you look like messages for everyone', text: "When a lecturer names you, it's easy to miss." },
]

const STEPS = [
  {
    title: 'Sign up with your student email',
    text: (
      <>
        Use your <span className="rounded-md bg-muted px-1.5">@student.aiu.edu.my</span> address and open the
        activation link sent to you.
      </>
    ),
  },
  { title: 'Choose your studies', text: 'Pick your school, programme and intake, so UniFlow knows which courses are yours.' },
  { title: 'Add your groups and timetable', text: "Add the WhatsApp and Telegram groups you're in, and upload or paste your timetable." },
  { title: 'Read what matters', text: 'Check "For you", get alerts, and confirm class changes on your timetable.' },
]

type Feature = { tag: string; title: string; text: string; desktop: string; phone: string; alt: string }

const FEATURES: Feature[] = [
  {
    tag: 'For you',
    title: 'What needs you comes first',
    text: "Messages that name you and things you have to do sit at the top, then important updates. Every item says why you're seeing it and links to the original message.",
    desktop: announcement,
    phone: phoneAnnouncement,
    alt: 'An announcement about a moved class, with the group message it came from',
  },
  {
    tag: 'Timetable',
    title: 'Class changes, confirmed by you',
    text: 'Your week in one place. When a group announces a moved or cancelled class, the change waits for you to confirm before your timetable updates.',
    desktop: timetableWeek,
    phone: phoneTimetable,
    alt: 'The timetable, with a class change waiting to be confirmed',
  },
  {
    tag: 'Search',
    title: 'Find anything from your groups',
    text: 'Search every announcement by word, like "internship" or "quiz", instead of scrolling back through each chat.',
    desktop: search,
    phone: phoneSearch,
    alt: 'Search results for "internship"',
  },
  {
    tag: 'Notifications and digest',
    title: 'Alerts when it counts',
    text: 'Get an alert when something needs you, and a short daily digest of everything else.',
    desktop: notifications,
    phone: phoneNotifications,
    alt: 'The notifications page in the dark theme',
  },
]

const TRUST: { icon: LucideIcon; title: string; text: string }[] = [
  { icon: CircleDot, title: 'Only groups you add', text: 'UniFlow reads the academic groups students add, nothing else.' },
  { icon: ArrowUpRight, title: 'Always linked to the source', text: 'Every summary shows the original message, its group and its time.' },
  { icon: Check, title: 'You stay in control', text: 'A class change only applies to your timetable when you confirm it.' },
]

/** A screenshot: the desktop image from 768 px up, the phone image (in a phone frame) below. */
function Screenshot({ desktop, phone, alt, eager = false }: { desktop: string; phone: string; alt: string; eager?: boolean }) {
  return (
    <picture className="mx-auto block w-[72%] max-w-xs overflow-hidden rounded-[1.75rem] bg-card ring-[5px] ring-foreground md:w-full md:max-w-none md:rounded-2xl md:shadow-[0_24px_60px_-28px_rgb(20_20_15/0.35)] md:ring-1 md:ring-border">
      <source media="(min-width: 768px)" srcSet={desktop} width={1440} height={900} />
      <img
        src={phone}
        alt={alt}
        width={780}
        height={1688}
        loading={eager ? 'eager' : 'lazy'}
        className="block h-auto w-full"
      />
    </picture>
  )
}

function Kicker({ children }: { children: string }) {
  return <p className="text-sm font-medium tracking-[0.08em] text-muted-foreground uppercase">{children}</p>
}

const h2 = 'mt-3 max-w-[18ch] text-[2rem] leading-[1.05] font-medium tracking-[-0.03em] text-balance md:text-[2.75rem]'
const sub = 'mt-4 max-w-[60ch] text-[1.0625rem] leading-relaxed text-muted-foreground md:text-lg'

/** The public home page: what UniFlow is and how to use it (shown at / to visitors who are not logged in). */
export function HomePage() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <header className="bg-primary text-primary-foreground">
        <div className="mx-auto flex h-16 max-w-6xl items-center gap-3 px-5 md:h-18 md:gap-8 md:px-8">
          <Link to="/" className={cn('rounded-sm text-xl', onLimeFocus)}>
            <Wordmark inverted />
          </Link>
          <nav aria-label="Home page" className="ml-4 hidden gap-7 text-[0.9375rem] sm:flex">
            <a href="#how-it-works" className={cn('rounded-sm hover:underline hover:underline-offset-4', onLimeFocus)}>
              How it works
            </a>
            <a href="#features" className={cn('rounded-sm hover:underline hover:underline-offset-4', onLimeFocus)}>
              Features
            </a>
          </nav>
          <div className="ml-auto flex gap-2.5">
            <Button asChild variant="outline" size="sm" className={inkOutline}>
              <Link to="/login">Log in</Link>
            </Button>
            <Button asChild size="sm" className={inkButton}>
              <Link to="/register">Sign up</Link>
            </Button>
          </div>
        </div>
      </header>

      <main>
        {/* Opening: the lime band, with the screenshot hanging over its bottom edge. */}
        <div className="rounded-b-[1.75rem] bg-primary pt-7 text-primary-foreground md:rounded-b-[2.5rem] md:pt-14">
          <div className="mx-auto max-w-6xl px-5 md:px-8">
            <p className="text-[0.9375rem]">For Albukhary International University students</p>
            <h1 className="mt-3 max-w-[13ch] text-[2.625rem] leading-[0.98] font-medium tracking-[-0.035em] md:mt-4 md:text-[4.5rem]">
              All your AIU announcements, sorted for you
            </h1>
            <p className="mt-5 max-w-[56ch] text-[1.0625rem] leading-relaxed md:text-[1.1875rem]">
              UniFlow reads the academic WhatsApp and Telegram groups you add and puts what matters first: messages
              that name you, deadlines, and class changes.
            </p>
            <div className="mt-7 flex gap-3">
              <Button asChild size="lg" className={cn('flex-1 px-6 md:flex-none', inkButton)}>
                <Link to="/register">Sign up</Link>
              </Button>
              <Button asChild size="lg" variant="outline" className={cn('flex-1 px-6 md:flex-none', inkOutline)}>
                <Link to="/login">Log in</Link>
              </Button>
            </div>
            <div className="relative -mb-36 pt-10 md:-mb-30 md:pt-14">
              <Screenshot desktop={forYou} phone={phoneForYou} alt="The For you page: what needs you, today's classes and important updates" eager />
            </div>
          </div>
        </div>

        <section aria-labelledby="problem" className="pt-52 pb-16 md:pt-50 md:pb-24">
          <div className="mx-auto grid max-w-6xl gap-8 px-5 md:grid-cols-2 md:gap-16 md:px-8">
            <div>
              <Kicker>The problem</Kicker>
              <h2 id="problem" className={h2}>Important messages get buried</h2>
              <p className={sub}>
                Course, school and club groups never stop. The one message that moves your class or names you sits
                between everything else.
              </p>
            </div>
            <ul className="border-t border-border">
              {PROBLEMS.map((problem) => (
                <li key={problem.title} className="flex gap-4 border-b border-border py-5">
                  <span aria-hidden className="mt-0.5 flex size-7 shrink-0 items-center justify-center rounded-full border-[1.5px] border-foreground">
                    <X className="size-3.5" />
                  </span>
                  <div>
                    <p className="text-lg font-medium">{problem.title}</p>
                    <p className="mt-0.5 text-muted-foreground">{problem.text}</p>
                  </div>
                </li>
              ))}
            </ul>
          </div>
        </section>

        <section id="how-it-works" aria-labelledby="how" className="scroll-mt-6 pb-16 md:pb-24">
          <div className="mx-auto max-w-6xl px-5 md:px-8">
            <Kicker>How it works</Kicker>
            <h2 id="how" className={h2}>How to use UniFlow</h2>
            <p className={sub}>Four steps, a few minutes. After that, UniFlow keeps up with your groups for you.</p>
            <ol className="mt-8 grid gap-3 md:mt-12 md:grid-cols-2 md:gap-4 lg:grid-cols-4">
              {STEPS.map((step, index) => (
                <li
                  key={step.title}
                  className="grid grid-cols-[2.75rem_1fr] gap-x-4 rounded-2xl bg-card p-5 ring-1 ring-border lg:block lg:p-7"
                >
                  <span aria-hidden className="flex size-11 items-center justify-center rounded-full bg-primary text-lg font-semibold text-primary-foreground">
                    {index + 1}
                  </span>
                  <h3 className="self-center text-lg leading-snug font-medium lg:mt-7">{step.title}</h3>
                  <p className="col-start-2 mt-1 text-[0.9375rem] leading-relaxed text-muted-foreground lg:mt-2.5">{step.text}</p>
                </li>
              ))}
            </ol>
          </div>
        </section>

        <div className="mx-auto max-w-6xl px-5 md:px-8">
          <section id="features" aria-labelledby="features-title" className="scroll-mt-6 rounded-[1.75rem] bg-card px-5 py-14 md:rounded-[2.5rem] md:px-16 md:py-24">
            <Kicker>Features</Kicker>
            <h2 id="features-title" className={h2}>What UniFlow does for you</h2>
            {FEATURES.map((feature, index) => (
              <div
                key={feature.tag}
                className={cn(
                  'mt-14 grid items-center gap-6 md:mt-22 md:gap-16',
                  index % 2 ? 'md:grid-cols-[7fr_5fr]' : 'md:grid-cols-[5fr_7fr]',
                )}
              >
                <div className={cn(index % 2 && 'md:order-2')}>
                  <p className="flex items-center gap-2 text-sm font-medium">
                    <span aria-hidden className="size-2.5 rounded-full bg-primary ring-[1.5px] ring-foreground" />
                    {feature.tag}
                  </p>
                  <h3 className="mt-2.5 text-2xl leading-tight font-medium tracking-[-0.02em] md:text-[1.875rem]">{feature.title}</h3>
                  <p className="mt-3.5 leading-relaxed text-muted-foreground md:text-[1.0625rem]">{feature.text}</p>
                </div>
                <Screenshot desktop={feature.desktop} phone={feature.phone} alt={feature.alt} />
              </div>
            ))}
          </section>
        </div>

        <section aria-labelledby="trust" className="py-16 md:py-24">
          <div className="mx-auto max-w-6xl px-5 md:px-8">
            <div className="island rounded-[1.75rem] px-6 py-9 md:rounded-[2rem] md:p-16">
              <h2 id="trust" className="text-[2rem] leading-[1.05] font-medium tracking-[-0.03em] md:text-[2.75rem]">
                Built to be trusted
              </h2>
              <p className="mt-4 text-island-muted md:text-lg">
                Read how UniFlow uses information in the{' '}
                <Link
                  to="/privacy"
                  className="rounded-sm text-primary underline underline-offset-4 outline-none hover:decoration-2 focus-visible:ring-3 focus-visible:ring-primary"
                >
                  privacy notice
                </Link>
                .
              </p>
              <ul className="mt-9 grid gap-7 md:mt-12 md:grid-cols-3 md:gap-8">
                {TRUST.map(({ icon: Icon, title, text }) => (
                  <li key={title}>
                    <span aria-hidden className="flex size-10 items-center justify-center rounded-full border-[1.5px] border-primary text-primary">
                      <Icon className="size-4.5" />
                    </span>
                    <p className="mt-4 text-lg font-medium">{title}</p>
                    <p className="mt-1.5 leading-relaxed text-island-muted">{text}</p>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </section>

        <section aria-labelledby="start" className="pb-12 md:pb-16">
          <div className="mx-auto max-w-6xl px-5 md:px-8">
            <div className="rounded-[1.75rem] bg-primary px-6 py-12 text-center text-primary-foreground md:rounded-[2.5rem] md:px-16 md:py-20">
              <h2 id="start" className="text-[2rem] leading-[1.05] font-medium tracking-[-0.03em] md:text-[2.75rem]">
                Ready to start?
              </h2>
              <p className="mt-3.5 md:text-lg">
                Sign-up needs an AIU student email (<span className="font-semibold">@student.aiu.edu.my</span>).
              </p>
              <div className="mt-7 flex flex-col justify-center gap-3 sm:flex-row">
                <Button asChild size="lg" className={cn('px-6', inkButton)}>
                  <Link to="/register">Sign up</Link>
                </Button>
                <Button asChild size="lg" variant="outline" className={cn('px-6', inkOutline)}>
                  <Link to="/login">Log in</Link>
                </Button>
              </div>
            </div>
          </div>
        </section>
      </main>

      <footer className="mx-auto max-w-6xl px-5 pb-12 md:px-8 md:pb-14">
        <div className="flex flex-wrap items-center gap-x-7 gap-y-3 border-t border-border pt-8 text-[0.9375rem] text-muted-foreground">
          <Link to="/" className="rounded-sm text-lg text-foreground outline-none focus-visible:ring-3 focus-visible:ring-ring">
            <Wordmark />
          </Link>
          <Link to="/privacy" className="inline-flex min-h-11 items-center rounded-sm underline-offset-4 outline-none hover:underline focus-visible:ring-3 focus-visible:ring-ring md:min-h-0">
            Privacy notice
          </Link>
          <Link to="/login" className="inline-flex min-h-11 items-center rounded-sm underline-offset-4 outline-none hover:underline focus-visible:ring-3 focus-visible:ring-ring md:min-h-0">
            Log in
          </Link>
          <p className="w-full md:ml-auto md:w-auto">For Albukhary International University students</p>
        </div>
      </footer>
    </div>
  )
}
