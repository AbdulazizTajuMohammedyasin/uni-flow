import { zodResolver } from '@hookform/resolvers/zod'
import { useEffect, useRef, useState } from 'react'
import { useForm } from 'react-hook-form'
import { CircleAlert, CircleCheck } from 'lucide-react'
import { Link, useParams } from 'react-router'
import { z } from 'zod'

import { activateAccount, resendActivation } from '@/api/auth'
import { ApiError } from '@/api/errors'
import { FormField } from '@/components/FormField'
import { ResultIcon } from '@/components/ResultIcon'
import { Button } from '@/components/ui/button'

type Status = 'activating' | 'activated' | 'already-used' | 'invalid' | 'error'

const resendSchema = z.object({ email: z.email('Enter a valid email address.') })
type ResendForm = z.infer<typeof resendSchema>

/** Opened from the activation email: /verify-email/:uid/:token */
export function ActivateAccountPage() {
  const { uid = '', token = '' } = useParams()
  const [status, setStatus] = useState<Status>('activating')
  const started = useRef(false)

  useEffect(() => {
    // React runs effects twice in development; a link must only be used once.
    if (started.current) return
    started.current = true
    activateAccount(uid, token)
      .then(() => setStatus('activated'))
      .catch((error) => {
        if (error instanceof ApiError && error.status === 403) setStatus('already-used')
        else if (error instanceof ApiError && error.status === 400) setStatus('invalid')
        else setStatus('error')
      })
  }, [uid, token])

  if (status === 'activating') {
    return <p role="status" className="text-center text-muted-foreground">Activating your account…</p>
  }

  if (status === 'activated' || status === 'already-used') {
    return (
      <div className="text-center">
        <ResultIcon icon={CircleCheck} tone="success" />
        <h1 className="text-[1.75rem] leading-tight font-medium tracking-[-0.025em] sm:text-[2rem]">
          {status === 'activated' ? 'Your account is active' : 'Account already activated'}
        </h1>
        <p className="mt-3 text-sm text-muted-foreground">You can now log in to UniFlow.</p>
        <Button asChild size="lg" className="mt-6 w-full">
          <Link to="/login">Log in</Link>
        </Button>
      </div>
    )
  }

  return (
    <div>
      <ResultIcon icon={CircleAlert} tone="destructive" />
      <h1 className="text-center text-[1.75rem] leading-tight font-medium tracking-[-0.025em] sm:text-[2rem]">This link didn't work</h1>
      <p className="mt-3 text-center text-sm text-muted-foreground">
        {status === 'invalid'
          ? 'The activation link is invalid or incomplete.'
          : 'Something went wrong while activating your account.'}{' '}
        Enter your student email and we'll send a new link.
      </p>
      <ResendActivation />
    </div>
  )
}

function ResendActivation() {
  const [sent, setSent] = useState(false)
  const {
    register,
    handleSubmit,
    setError,
    formState: { errors, isSubmitting },
  } = useForm<ResendForm>({ resolver: zodResolver(resendSchema) })

  async function onSubmit({ email }: ResendForm) {
    try {
      await resendActivation(email)
      setSent(true)
    } catch (error) {
      setError('root', {
        message: error instanceof ApiError ? error.message : 'Something went wrong. Please try again.',
      })
    }
  }

  if (sent) {
    return (
      <p role="status" className="mt-6 text-sm">
        If that account is waiting for activation, a new link is on its way. Check your email.
      </p>
    )
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} noValidate className="mt-6 space-y-4">
      <FormField
        label="Student email"
        type="email"
        autoComplete="email"
        error={errors.email?.message}
        {...register('email')}
      />
      {errors.root && (
        <p role="alert" className="text-sm text-destructive">
          {errors.root.message}
        </p>
      )}
      <Button type="submit" size="lg" className="w-full" disabled={isSubmitting}>
        {isSubmitting ? 'Sending…' : 'Send a new activation link'}
      </Button>
    </form>
  )
}
