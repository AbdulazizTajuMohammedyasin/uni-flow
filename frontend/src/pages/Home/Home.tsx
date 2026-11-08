import { ArrowUpRight, AtSign, Check, CircleDot, Clock, MessagesSquare, type LucideIcon } from 'lucide-react'
import { Link } from 'react-router'

import { Button } from '@/components/ui/button'
import { Wordmark } from '@/components/Wordmark'
import { cn } from '@/lib/utils'

// Screenshots of the real app with made-up data (e2e/mock-api.ts), made by `npm run screens:readme`.
// Each comes in both themes; the page shows the one that matches the visitor's theme.
import forYouDark from '@/assets/home/for-you-dark.png'
import forYou from '@/assets/home/for-you.png'
import phoneAnnouncementDark from '@/assets/home/phone-announcement-dark.png'
import phoneAnnouncement from '@/assets/home/phone-announcement.png'
import phoneForYouDark from '@/assets/home/phone-for-you-dark.png'
import phoneForYou from '@/assets/home/phone-for-you.png'
import phoneNotificationsDark from '@/assets/home/phone-notifications-dark.png'
import phoneNotifications from '@/assets/home/phone-notifications.png'
import phoneSearchDark from '@/assets/home/phone-search-dark.png'
import phoneSearch from '@/assets/home/phone-search.png'
import phoneTimetableDark from '@/assets/home/phone-timetable-dark.png'
import phoneTimetable from '@/assets/home/phone-timetable.png'

/** A screenshot in the light and dark themes. */
type Shot = { light: string; dark: string }

const focusRing = 'outline-none focus-visible:ring-3 focus-visible:ring-ring'

const PROBLEMS: { icon: LucideIcon; title: string; text: string }[] = [
  { icon: MessagesSquare, title: 'Class changes scroll away', text: 'A room change is posted once, then lost under the replies.' },
  { icon: Clock, title: 'Deadlines are mentioned in passing', text: 'A due date hides in the middle of a long message.' },
  { icon: AtSign, title: 'Messages for you look like messages for everyone', text: "When a lecturer names you, it's easy to miss." },
]

const STEPS = [
  {
    title: 'Sign up with your student email',
    text: (
      <>
        Use your <span className="rounded-md bg-muted px-1.5 text-foreground">@student.aiu.edu.my</span> address and
        open the activation link sent to you.
      </>
    ),
  },
  { title: 'Choose your studies', text: 'Pick your school, programme and intake, so UniFlow knows which courses are yours.' },
  { title: 'Add your groups and timetable', text: "Add the WhatsApp and Telegram groups you're in, and upload or paste your timetable." },
  { title: 'Read what matters', text: 'Check "For you", get alerts, and confirm class changes on your timetable.' },
]

type Feature = { tag: string; title: string; text: string; points: string[]; phone: Shot; alt: string }

const FEATURES: Feature[] = [
  {
    tag: 'For you',
    title: 'What needs you comes first',
    text: "Messages that name you and things you have to do sit at the top, then important updates. Every item says why you're seeing it and links to the original message.",
    points: ['Named in a message, or something to do: always on top', 'The original message, its group and its time'],
    phone: { light: phoneAnnouncement, dark: phoneAnnouncementDark },
    alt: 'An announcement about a moved class, with the group message it came from',
  },
  {
    tag: 'Timetable',
    title: 'Class changes, confirmed by you',
    text: 'Your week in one place. When a group announces a moved or cancelled class, the change waits for you to confirm before your timetable updates.',
    points: ['Now and Next at a glance', 'This week only, or every week from now on'],
    phone: { light: phoneTimetable, dark: phoneTimetableDark },
    alt: 'The timetable, with a class change waiting to be confirmed',
  },
  {
    tag: 'Search',
    title: 'Find anything from your groups',
    text: 'Search every announcement by word, like "internship" or "quiz", instead of scrolling back through each chat.',
    points: ['Every group you added, in one search'],
    phone: { light: phoneSearch, dark: phoneSearchDark },
    alt: 'Search results for "internship"',
  },
  {
    tag: 'Notifications and digest',
    title: 'Alerts when it counts',
    text: 'Get an alert when something needs you, and a short daily digest of everything else.',
    points: ['A "Needs you" tab for what must not be missed', 'One short digest a day for the rest'],
    phone: { light: phoneNotifications, dark: phoneNotificationsDark },
    alt: 'The notifications page, with alerts for what needs you',
  },
]

const TRUST: { icon: LucideIcon; title: string; text: string }[] = [
  { icon: CircleDot, title: 'Only groups you add', text: 'UniFlow reads the academic groups students add, nothing else.' },
  { icon: ArrowUpRight, title: 'Always linked to the source', text: 'Every summary shows the original message, its group and its time.' },
  { icon: Check, title: 'You stay in control', text: 'A class change only applies to your timetable when you confirm it.' },
]

/** Both themes of a screenshot; only the one for the current theme is shown (and, being lazy, loaded). */
function ThemedImage({ shot, alt, width, height, className }: { shot: Shot; alt: string; width: number; height: number; className: string }) {
  return (
    <>
      <img src={shot.light} alt={alt} width={width} height={height} loading="lazy" className={cn(className, 'dark:hidden')} />
      <img src={shot.dark} alt={alt} width={width} height={height} loading="lazy" className={cn(className, 'hidden dark:block')} />
    </>
  )
}

/** A phone screenshot in a drawn phone: dark bezel, camera pill and side button. */
function Phone({ shot, alt, className }: { shot: Shot; alt: string; className?: string }) {
  return (
    <div className={cn('relative rounded-[3rem] bg-phone-frame p-2.5 shadow-shot', className)}>
      <span aria-hidden className="absolute top-5 left-1/2 z-10 h-5.5 w-19 -translate-x-1/2 rounded-full bg-phone-frame" />
      <span aria-hidden className="absolute top-30 -right-0.75 h-16 w-0.75 rounded-r-sm bg-phone-frame" />
      <ThemedImage
        shot={shot}
        alt={alt}
        width={780}
        height={1688}
        className="block aspect-[390/844] h-auto w-full rounded-[2.375rem] object-cover object-top"
      />
    </div>
  )
}

/** The centred kicker, heading and line that open each section. */
function SectionTitle({ id, kicker, title, children }: { id: string; kicker: string; title: string; children?: string }) {
  return (
    <div className="mx-auto max-w-3xl text-center">
      <p className="text-sm font-semibold tracking-[0.08em] text-muted-foreground uppercase">{kicker}</p>
      <h2 id={id} className="mt-3.5 text-[2rem] leading-[1.06] font-semibold tracking-[-0.03em] text-balance md:text-[2.875rem]">
        {title}
      </h2>
      {children && <p className="mx-auto mt-3.5 max-w-[60ch] text-[1.0625rem] leading-relaxed text-muted-foreground md:text-lg">{children}</p>}
    </div>
  )
}

/** The public home page: what UniFlow is and how to use it (shown at / to visitors who are not logged in). */
export function HomePage() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <header className="border-b border-border bg-card">
        <div className="mx-auto flex h-16 max-w-6xl items-center gap-3 px-5 md:h-18 md:gap-8 md:px-8">
          <Link to="/" className={cn('rounded-sm text-xl', focusRing)}>
            <Wordmark />
          </Link>
          <nav aria-label="Home page" className="ml-4 hidden gap-7 text-[0.9375rem] font-medium sm:flex">
            <a href="#how-it-works" className={cn('rounded-sm hover:underline hover:underline-offset-4', focusRing)}>
              How it works
            </a>
            <a href="#features" className={cn('rounded-sm hover:underline hover:underline-offset-4', focusRing)}>
              Features
            </a>
          </nav>
          <div className="ml-auto flex gap-2.5">
            <Button asChild variant="outline" size="sm">
              <Link to="/login">Log in</Link>
            </Button>
            <Button asChild size="sm">
              <Link to="/register">Sign up</Link>
            </Button>
          </div>
        </div>
      </header>

      <main>
        {/* Opening: centred text on the page colour fading into a soft blue wash, with rounded bottom corners.
            Below it, the For you page in a browser window (computers) or a phone (smaller screens). */}
        <div className="hero-wash rounded-b-[2rem] px-5 pt-11 pb-14 md:rounded-b-[3rem] md:px-8 md:pt-22 md:pb-24">
          <div className="mx-auto flex max-w-6xl flex-col items-center text-center">
            <p className="rounded-full bg-tag px-3.5 py-1 text-[0.8125rem] font-medium text-tag-foreground md:text-[0.9375rem]">
              For Albukhary International University students
            </p>
            <h1 className="mt-5 max-w-[15ch] text-[2.625rem] leading-[1.04] font-semibold tracking-[-0.04em] text-balance md:mt-6 md:text-[4.75rem]">
              All your AIU announcements, sorted for you
            </h1>
            <p className="mt-5 max-w-[40rem] text-[1.0625rem] leading-relaxed md:mt-6 md:text-[1.1875rem]">
              UniFlow reads the academic WhatsApp and Telegram groups you add and puts what matters first: messages that
              name you, deadlines, and class changes.
            </p>
            <div className="mt-7 flex w-full justify-center gap-3 md:mt-8 md:w-auto">
              <Button asChild size="lg" variant="outline" className="flex-1 bg-card px-6 md:flex-none">
                <Link to="/login">Log in</Link>
              </Button>
              <Button asChild size="lg" className="flex-1 px-6 md:flex-none">
                <Link to="/register">Sign up</Link>
              </Button>
            </div>

            <div className="mt-14 hidden w-full max-w-[1080px] overflow-hidden rounded-[1.375rem] bg-card text-left shadow-shot ring-1 ring-border md:block">
              <div aria-hidden className="flex h-11 items-center gap-2 border-b border-border bg-muted px-4.5">
                <span className="size-2.75 rounded-full bg-muted-foreground/30" />
                <span className="size-2.75 rounded-full bg-muted-foreground/30" />
                <span className="size-2.75 rounded-full bg-muted-foreground/30" />
                <span className="mx-auto -translate-x-6 rounded-full bg-card px-4.5 py-1 text-[0.8125rem] text-muted-foreground">
                  UniFlow · For you
                </span>
              </div>
              <div className="aspect-[1440/800] overflow-hidden">
                <ThemedImage
                  shot={{ light: forYou, dark: forYouDark }}
                  alt="The For you page: what needs you, important updates and today's classes"
                  width={1440}
                  height={900}
                  className="block w-full"
                />
              </div>
            </div>
            <Phone
              shot={{ light: phoneForYou, dark: phoneForYouDark }}
              alt="The For you page on a phone: today's classes and what needs you"
              className="mt-10 w-[16.25rem] md:hidden"
            />
          </div>
        </div>

        <section aria-labelledby="problem" className="px-5 pt-18 pb-16 md:px-8 md:pt-28 md:pb-28">
          <div className="mx-auto max-w-6xl">
            <SectionTitle id="problem" kicker="The problem" title="Important messages get buried">
              Course, school and club groups never stop. The one message that moves your class or names you sits between
              everything else.
            </SectionTitle>
            <ul className="mt-8 grid gap-3.5 md:mt-14 md:grid-cols-3 md:gap-5">
              {PROBLEMS.map(({ icon: Icon, title, text }) => (
                <li key={title} className="rounded-[1.25rem] bg-card p-6 shadow-card md:p-7">
                  <span aria-hidden className="flex size-10.5 items-center justify-center rounded-full bg-muted text-muted-foreground">
                    <Icon className="size-5" />
                  </span>
                  <p className="mt-4 text-lg leading-snug font-semibold md:text-[1.1875rem]">{title}</p>
                  <p className="mt-2 leading-relaxed text-muted-foreground">{text}</p>
                </li>
              ))}
            </ul>
          </div>
        </section>

        <section id="how-it-works" aria-labelledby="how" className="scroll-mt-6 px-5 pb-16 md:px-8 md:pb-28">
          <div className="mx-auto max-w-6xl">
            <SectionTitle id="how" kicker="How it works" title="How to use UniFlow">
              Four steps, a few minutes. After that, UniFlow keeps up with your groups for you.
            </SectionTitle>
            {/* A dashed line joins the numbers: down the side on phones, across the top on wide screens. */}
            <ol
              className={cn(
                'relative mt-8 grid gap-3.5 md:mt-14 md:grid-cols-2 md:gap-5 lg:grid-cols-4',
                "before:absolute before:top-10 before:bottom-10 before:left-10.25 before:border-l-2 before:border-dashed before:border-island-border before:content-['']",
                'md:before:hidden lg:before:block lg:before:top-12.25 lg:before:right-[12%] lg:before:bottom-auto lg:before:left-[12%] lg:before:border-t-2 lg:before:border-l-0',
              )}
            >
              {STEPS.map((step, index) => (
                <li
                  key={step.title}
                  className="relative grid grid-cols-[2.75rem_1fr] gap-x-4 rounded-[1.25rem] bg-card p-5 shadow-card lg:block lg:p-7"
                >
                  <span
                    aria-hidden
                    className="row-span-2 flex size-11 items-center justify-center rounded-full bg-primary text-lg font-semibold text-primary-foreground ring-6 ring-card"
                  >
                    {index + 1}
                  </span>
                  <h3 className="self-center text-lg leading-snug font-semibold lg:mt-6">{step.title}</h3>
                  <p className="mt-1 text-[0.9375rem] leading-relaxed text-muted-foreground lg:mt-2.5">{step.text}</p>
                </li>
              ))}
            </ol>
          </div>
        </section>

        <section id="features" aria-labelledby="features-title" className="scroll-mt-6 px-5 pb-16 md:px-8 md:pb-28">
          <div className="mx-auto max-w-6xl">
            <SectionTitle id="features-title" kicker="Features" title="What UniFlow does for you" />
            <div className="mt-8 grid gap-4.5 md:mt-14 md:gap-7">
              {FEATURES.map((feature, index) => {
                const flip = index % 2 === 1
                return (
                  <div key={feature.tag} className="relative overflow-hidden rounded-[1.25rem] bg-card shadow-card md:grid md:grid-cols-2">
                    {/* The wash behind the phone, fading out towards the text so the halves blend. */}
                    <span
                      aria-hidden
                      className={cn(
                        'stage-wash absolute inset-x-0 top-[30%] bottom-0 [mask-image:linear-gradient(to_bottom,transparent,#000_40%)] md:top-0',
                        flip
                          ? 'md:right-[30%] md:[mask-image:linear-gradient(to_left,transparent,#000_45%)]'
                          : 'md:left-[30%] md:[mask-image:linear-gradient(to_right,transparent,#000_45%)]',
                      )}
                    />
                    <div className="relative z-10 grid content-center gap-3.5 px-6 pt-7 md:p-16">
                      <p className="flex items-center gap-2 text-sm font-semibold text-link md:text-[0.9375rem]">
                        <span aria-hidden className="size-2.25 rounded-full bg-primary" />
                        {feature.tag}
                      </p>
                      <h3 className="text-[1.625rem] leading-[1.12] font-semibold tracking-[-0.025em] text-balance md:text-[2.125rem]">
                        {feature.title}
                      </h3>
                      <p className="leading-relaxed text-muted-foreground md:text-[1.0625rem]">{feature.text}</p>
                      <ul className="mt-1.5 grid gap-2 text-[0.9375rem] md:text-[0.96875rem]">
                        {feature.points.map((point) => (
                          <li key={point} className="flex items-start gap-2.5">
                            <Check aria-hidden className="mt-0.5 size-4.5 shrink-0 text-link" />
                            {point}
                          </li>
                        ))}
                      </ul>
                    </div>
                    <div className={cn('relative z-10 flex items-center justify-center px-5 pt-10 pb-12 md:p-14', flip && 'md:order-first')}>
                      <span aria-hidden className="absolute top-1/2 left-1/2 size-85 -translate-1/2 rounded-full border-[1.5px] border-dashed border-island-border md:size-115" />
                      <span aria-hidden className="phone-glow absolute top-1/2 left-1/2 size-75 -translate-1/2 rounded-full md:size-95" />
                      <Phone shot={feature.phone} alt={feature.alt} className="w-55 md:w-67.5" />
                      {/* The feature's first point again, as a small card resting on the phone. */}
                      <p
                        aria-hidden
                        className={cn(
                          'absolute bottom-7.5 flex max-w-48 items-center gap-2 rounded-[0.875rem] bg-card px-3.5 py-2.5 text-[0.8125rem] leading-snug font-medium shadow-shot ring-1 ring-border md:bottom-16 md:max-w-58 md:text-[0.84375rem]',
                          flip ? 'right-3.5 md:right-7' : 'left-3.5 md:left-7',
                        )}
                      >
                        <span className="flex size-5 shrink-0 items-center justify-center rounded-full bg-primary text-primary-foreground">
                          <Check className="size-3.5" strokeWidth={2.75} />
                        </span>
                        {feature.points[0]}
                      </p>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        </section>

        <section aria-labelledby="trust" className="px-5 pb-16 md:px-8 md:pb-28">
          <div className="island mx-auto max-w-6xl rounded-[1.5rem] px-6 py-9 md:rounded-[1.75rem] md:p-16">
            <h2 id="trust" className="text-[2rem] leading-[1.05] font-semibold tracking-[-0.03em] md:text-[2.875rem]">
              Built to be trusted
            </h2>
            <p className="mt-3.5 text-island-muted md:text-lg">
              Read how UniFlow uses information in the{' '}
              <Link
                to="/privacy"
                className="rounded-sm font-medium text-island-accent underline underline-offset-4 outline-none hover:decoration-2 focus-visible:ring-3 focus-visible:ring-ring"
              >
                privacy notice
              </Link>
              .
            </p>
            <ul className="mt-9 grid gap-7 md:mt-11 md:grid-cols-3 md:gap-8">
              {TRUST.map(({ icon: Icon, title, text }) => (
                <li key={title}>
                  <span aria-hidden className="flex size-11.5 items-center justify-center rounded-full bg-card text-island-accent shadow-card">
                    <Icon className="size-5" />
                  </span>
                  <p className="mt-4 text-lg font-semibold md:text-[1.1875rem]">{title}</p>
                  <p className="mt-1.5 leading-relaxed text-island-muted">{text}</p>
                </li>
              ))}
            </ul>
          </div>
        </section>

        <section aria-labelledby="start" className="px-5 pb-12 md:px-8 md:pb-28">
          <div className="cta-corner mx-auto max-w-6xl rounded-[1.5rem] px-5.5 py-16 text-center shadow-card md:rounded-[1.75rem] md:px-8 md:py-24">
            <h2 id="start" className="text-[2rem] leading-[1.05] font-semibold tracking-[-0.03em] md:text-[2.875rem]">
              Ready to start?
            </h2>
            <p className="mt-3.5 text-muted-foreground md:text-lg">
              Sign-up needs an AIU student email (<span className="font-semibold text-foreground">@student.aiu.edu.my</span>).
            </p>
            <div className="mt-7 flex flex-col justify-center gap-3 sm:flex-row md:mt-8">
              <Button asChild size="lg" className="px-6">
                <Link to="/register">Sign up</Link>
              </Button>
              <Button asChild size="lg" variant="outline" className="bg-card px-6">
                <Link to="/login">Log in</Link>
              </Button>
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
