import type { ReactNode } from 'react'
import { Link } from 'react-router'

/** /privacy — the privacy notice (docs/09-security.md). Public: anyone can read it before
 * registering, and members of a group UniFlow reads are pointed here by the join notice.
 * Keep it in plain words and in step with what UniFlow really does. */
export function PrivacyPage() {
  return (
    <article className="space-y-6 text-[0.9375rem] leading-relaxed md:text-base">
      <h1 className="text-[1.375rem] leading-tight font-semibold tracking-tight md:text-[1.75rem]">Privacy notice</h1>
      <p>
        UniFlow is a student information assistant for Albukhary International University. It reads academic
        group messages so that each student sees only the information that matters to them. This notice says
        what UniFlow reads, what it keeps, and what it never does.
      </p>

      <Part title="What UniFlow reads">
        <ul className="list-disc space-y-2 pl-5 marker:text-muted-foreground">
          <li>
            Messages in <strong>academic WhatsApp and Telegram groups</strong> that students added to UniFlow
            (UniFlow's own number or bot is a member, and it posts a notice when it joins), and messages students
            paste or upload from such groups.
          </li>
          <li>Timetable files and links that students upload or that are shared in those groups.</li>
          <li>
            Never private chats, and never anything on a student's own phone: students never give UniFlow their
            phone number or access to their WhatsApp.
          </li>
        </ul>
      </Part>

      <Part title="What UniFlow keeps, and for how long">
        <ul className="list-disc space-y-2 pl-5 marker:text-muted-foreground">
          <li>
            Message text and files are <strong>deleted after 60 days</strong>. What was learned from them (for
            example "class moved to 2 PM") is kept with a <strong>short quote</strong> of the original message, so
            students can check where it came from.
          </li>
          <li>Senders are recorded by name as shown in the group and a scrambled id, never a phone number.</li>
          <li>
            Your account: your university email, name, school, programme, intake, your classes, and the interests
            and nicknames you choose (nicknames are only used to notice when someone mentions you).
          </li>
        </ul>
      </Part>

      <Part title="Artificial intelligence">
        <p>
          To understand messages, UniFlow sends the message text (never your profile) to Google's Gemini AI
          service. UniFlow uses Gemini's <strong>free tier</strong>: under Google's terms for it, Google may use
          the text it receives to improve its products. Deciding what is relevant to you is done by UniFlow
          itself, not by the AI. A class change only changes your timetable when you confirm it.
        </p>
      </Part>

      <Part title="Your choices">
        <ul className="list-disc space-y-2 pl-5 marker:text-muted-foreground">
          <li>
            <strong>If you're in a group UniFlow reads and don't want your messages read</strong>, ask the UniFlow
            team: your messages will be skipped from then on, and the ones already stored will be erased. A group
            admin can also simply remove UniFlow's number or bot from the group.
          </li>
          <li>You can dismiss anything in your feed, or mark it "not relevant to me".</li>
          <li>
            Contact: the UniFlow team at Albukhary International University (contact details will be added before
            launch).
          </li>
        </ul>
      </Part>

      <p className="border-t border-border pt-5 text-sm text-muted-foreground">
        <Link to="/register" className="text-primary hover:underline">
          Create an account
        </Link>{' '}
        ·{' '}
        <Link to="/" className="text-primary hover:underline">
          Back to UniFlow
        </Link>
      </p>
    </article>
  )
}

function Part({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="space-y-2">
      <h2 className="text-lg font-semibold">{title}</h2>
      {children}
    </section>
  )
}
