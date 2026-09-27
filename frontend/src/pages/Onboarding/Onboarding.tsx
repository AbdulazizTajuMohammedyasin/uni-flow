import { Navigate, useNavigate } from 'react-router'

import { StudentDetailsForm } from '@/components/StudentDetailsForm'
import { useAuth } from '@/context/AuthContext'

/** /onboarding — new students choose their school, programme and intake once. */
export function OnboardingPage() {
  const { user } = useAuth()
  const navigate = useNavigate()

  // Staff, and students who already finished, have nothing to do here.
  if (user && (user.role !== 'student' || user.profile_complete)) {
    return <Navigate to="/" replace />
  }

  return (
    <div>
      <h1 className="text-2xl font-bold tracking-tight">Welcome, {user?.full_name.split(' ')[0]}</h1>
      <p className="mt-1 text-sm text-muted-foreground">
        Tell us what you study, so UniFlow can show you the announcements and events that matter
        to you.
      </p>
      <div className="mt-6">
        <StudentDetailsForm submitLabel="Continue" onSaved={() => navigate('/', { replace: true })} />
      </div>
    </div>
  )
}
