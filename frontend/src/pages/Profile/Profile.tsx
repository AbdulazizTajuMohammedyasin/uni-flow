import { Link, useNavigate } from 'react-router'
import type { ReactNode } from 'react'

import { ChangePasswordForm } from '@/components/ChangePasswordForm'
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

function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="rounded-2xl bg-card p-6 shadow-sm ring-1 ring-border">
      <h2 className="text-lg font-semibold">{title}</h2>
      <div className="mt-4">{children}</div>
    </section>
  )
}

/** /profile — your details, your studies, your password, and log out. */
export function ProfilePage() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  if (!user) return null

  async function handleLogout() {
    await logout()
    navigate('/login', { replace: true })
  }

  return (
    <div className="max-w-2xl space-y-6">
      <h1 className="text-2xl font-bold tracking-tight">Profile</h1>

      <Section title="Account">
        <dl className="grid gap-3 text-sm sm:grid-cols-[8rem_1fr]">
          <dt className="text-muted-foreground">Name</dt>
          <dd>{user.full_name}</dd>
          <dt className="text-muted-foreground">Email</dt>
          <dd>{user.email}</dd>
          <dt className="text-muted-foreground">Role</dt>
          <dd>{ROLE_LABELS[user.role] ?? user.role}</dd>
        </dl>
      </Section>

      {user.role === 'student' && (
        <>
          <Section title="Your studies">
            <StudentDetailsForm submitLabel="Save changes" withSemester />
          </Section>
          <Section title="Your interests">
            <PreferencesForm submitLabel="Save interests" />
          </Section>
        </>
      )}

      <Section title="Appearance">
        <p className="mb-3 text-sm text-muted-foreground">
          "System" follows your phone or computer setting.
        </p>
        <ThemeToggle />
      </Section>

      <Section title="Password">
        <ChangePasswordForm />
      </Section>

      <Section title="Privacy">
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
  )
}
