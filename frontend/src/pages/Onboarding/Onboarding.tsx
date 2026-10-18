import { useState } from 'react'
import { Navigate, useNavigate } from 'react-router'

import { PreferencesForm } from '@/components/PreferencesForm'
import { StudentDetailsForm } from '@/components/StudentDetailsForm'
import { Button } from '@/components/ui/button'
import { useAuth } from '@/context/AuthContext'

/** "Step 1 of 2" with a two-part bar, so new students know how much is left. */
function Steps({ current }: { current: 1 | 2 }) {
  return (
    <div className="mb-5 space-y-2">
      <p className="text-xs font-semibold text-muted-foreground">
        Step {current} of 2 · {current === 1 ? 'Your studies' : 'Your interests (optional)'}
      </p>
      <div aria-hidden className="grid grid-cols-2 gap-1.5">
        <span className="h-1 rounded-full bg-primary" />
        <span className={`h-1 rounded-full ${current === 2 ? 'bg-primary' : 'bg-muted'}`} />
      </div>
    </div>
  )
}

/** /onboarding — new students choose what they study, then (optionally) their interests. */
export function OnboardingPage() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [step, setStep] = useState<'studies' | 'preferences'>('studies')
  const goHome = () => navigate('/', { replace: true })

  // Staff, and students who already finished, have nothing to do here.
  if (user && (user.role !== 'student' || (user.profile_complete && step === 'studies'))) {
    return <Navigate to="/" replace />
  }

  if (step === 'preferences') {
    return (
      <div>
        <Steps current={2} />
        <h1 className="text-2xl font-semibold tracking-tight">What matters to you?</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          UniFlow puts these first and keeps the rest out of your way. You can change them later
          in your profile.
        </p>
        <div className="mt-6 space-y-3">
          <PreferencesForm submitLabel="Finish" onSaved={goHome} />
          <Button variant="ghost" className="w-full" onClick={goHome}>
            Skip for now
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div>
      <Steps current={1} />
      <h1 className="text-2xl font-semibold tracking-tight">Welcome, {user?.full_name.split(' ')[0]}</h1>
      <p className="mt-1 text-sm text-muted-foreground">
        Tell us what you study, so UniFlow can show you the information that matters to you.
      </p>
      <div className="mt-6">
        <StudentDetailsForm submitLabel="Continue" onSaved={() => setStep('preferences')} />
      </div>
    </div>
  )
}
