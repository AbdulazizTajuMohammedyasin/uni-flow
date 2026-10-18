import { Link, useNavigate } from 'react-router'
import type { ReactNode } from 'react'

import { ChangePasswordForm } from '@/components/ChangePasswordForm'
import { PageHeader } from '@/components/PageHeader'
import { PreferencesForm } from '@/components/PreferencesForm'
import { StudentDetailsForm } from '@/components/StudentDetailsForm'
import { ThemeToggle } from '@/components/ThemeToggle'
import { Button } from '@/components/ui/button'
import { useAuth } from '@/context/AuthContext'

const ROLE_LABELS: Record<string, string> = {
  student: 'Student',
  lecturer: 'Lecturer',
  school_staff: 'School staff',
  university_admin: 'University admin',
  super_admin: 'Super admin',
}

type SectionInfo = { id: string; title: string }

const ACCOUNT = { id: 'account', title: 'Account' }
const STUDIES = { id: 'studies', title: 'Your studies' }
const INTERESTS = { id: 'interests', title: 'Your interests' }
const APPEARANCE = { id: 'appearance', title: 'Appearance' }
const PASSWORD = { id: 'password', title: 'Password' }
const PRIVACY = { id: 'privacy', title: 'Privacy' }

function Section({ id, title, description, children }: SectionInfo & { description?: string; children: ReactNode }) {
  return (
    // scroll-mt keeps the title clear of the phone top bar when jumped to from the section links.
    <section id={id} aria-labelledby={`${id}-title`} className="scroll-mt-20 rounded-xl bg-card p-5 ring-1 ring-border sm:p-6">
      <h2 id={`${id}-title`} className="text-lg font-semibold">
        {title}
      </h2>
      {description && <p className="mt-1 text-sm text-muted-foreground">{description}</p>}
      <div className="mt-4">{children}</div>
    </section>
  )
}

/** Links to each section: a row of chips on phones, a sticky list beside the sections on computers. */
function SectionNav({ sections }: { sections: SectionInfo[] }) {
  return (
    <nav aria-label="Profile sections" className="lg:sticky lg:top-8 lg:self-start">
      <ul className="flex flex-wrap gap-2 lg:flex-col lg:gap-0.5">
        {sections.map((section) => (
          <li key={section.id}>
            <a
              href={`#${section.id}`}
              className="inline-flex h-9 items-center rounded-full px-3.5 text-sm font-medium text-muted-foreground ring-1 ring-border hover:bg-muted hover:text-foreground lg:flex lg:rounded-md lg:px-3 lg:ring-0"
            >
              {section.title}
            </a>
          </li>
        ))}
      </ul>
    </nav>
  )
}

/** /profile — your details, your studies, your password, and log out. */
export function ProfilePage() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  if (!user) return null
  const student = user.role === 'student'

  async function handleLogout() {
    await logout()
    navigate('/login', { replace: true })
  }

  const sections = [ACCOUNT, ...(student ? [STUDIES, INTERESTS] : []), APPEARANCE, PASSWORD, PRIVACY]

  return (
    <div className="max-w-4xl space-y-6">
      <PageHeader title="Profile" />

      <div className="grid gap-6 lg:grid-cols-[11rem_minmax(0,1fr)] lg:gap-10">
        <SectionNav sections={sections} />

        <div className="max-w-2xl space-y-5">
          <Section {...ACCOUNT}>
            <dl className="grid gap-3 text-sm sm:grid-cols-[8rem_1fr]">
              <dt className="text-muted-foreground">Name</dt>
              <dd>{user.full_name}</dd>
              <dt className="text-muted-foreground">Email</dt>
              <dd className="break-all">{user.email}</dd>
              <dt className="text-muted-foreground">Role</dt>
              <dd>{ROLE_LABELS[user.role] ?? user.role}</dd>
            </dl>
          </Section>

          {student && (
            <>
              <Section {...STUDIES} description="UniFlow uses these to work out which announcements are meant for you.">
                <StudentDetailsForm submitLabel="Save changes" withSemester />
              </Section>
              <Section {...INTERESTS} description="UniFlow puts these first and keeps the rest out of your way.">
                <PreferencesForm submitLabel="Save interests" />
              </Section>
            </>
          )}

          <Section {...APPEARANCE} description={'"System" follows your phone or computer setting.'}>
            <ThemeToggle />
          </Section>

          <Section {...PASSWORD}>
            <ChangePasswordForm />
          </Section>

          <Section {...PRIVACY}>
            <p className="text-sm text-muted-foreground">
              What UniFlow reads, what it keeps (message text for 60 days), how it uses AI, and how someone can ask
              not to be read.{' '}
              <Link to="/privacy" className="font-medium text-primary hover:underline">
                Read the privacy notice
              </Link>
            </p>
          </Section>

          <Button variant="outline" onClick={handleLogout}>
            Log out
          </Button>
        </div>
      </div>
    </div>
  )
}
