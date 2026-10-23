import { zodResolver } from '@hookform/resolvers/zod'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { MailCheck } from 'lucide-react'
import { Link } from 'react-router'
import { z } from 'zod'

import { requestPasswordReset } from '@/api/auth'
import { ApiError } from '@/api/errors'
import { FormField } from '@/components/FormField'
import { ResultIcon } from '@/components/ResultIcon'
import { Button } from '@/components/ui/button'

const schema = z.object({ email: z.email('Enter a valid email address.') })
type ForgotForm = z.infer<typeof schema>

/** /forgot-password — ask for a password-reset link by email. */
export function ForgotPasswordPage() {
  const [sentTo, setSentTo] = useState<string | null>(null)
  const {
    register,
    handleSubmit,
    setError,
    formState: { errors, isSubmitting },
  } = useForm<ForgotForm>({ resolver: zodResolver(schema) })

  async function onSubmit({ email }: ForgotForm) {
    try {
      await requestPasswordReset(email)
      setSentTo(email)
    } catch (error) {
      setError('root', {
        message: error instanceof ApiError ? error.message : 'Something went wrong. Please try again.',
      })
    }
  }

  if (sentTo) {
    return (
      <div className="text-center">
        <ResultIcon icon={MailCheck} />
        <h1 className="text-2xl font-medium tracking-tight">Check your email</h1>
        <p className="mt-3 text-sm text-muted-foreground">
          If <span className="font-medium">{sentTo}</span> has a UniFlow account, we sent it a link
          to choose a new password.
        </p>
        <Button asChild size="lg" variant="outline" className="mt-6 w-full">
          <Link to="/login">Back to log in</Link>
        </Button>
      </div>
    )
  }

  return (
    <div>
      <h1 className="text-2xl font-medium tracking-tight">Forgot your password?</h1>
      <p className="mt-1 text-sm text-muted-foreground">
        Enter your email and we'll send you a link to choose a new one.
      </p>

      <form onSubmit={handleSubmit(onSubmit)} noValidate className="mt-6 space-y-4">
        <FormField
          label="Email"
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
          {isSubmitting ? 'Sending…' : 'Send reset link'}
        </Button>
      </form>

      <p className="mt-6 text-center text-sm text-muted-foreground">
        <Link to="/login" className="font-medium text-foreground underline underline-offset-4 hover:decoration-2">
          Back to log in
        </Link>
      </p>
    </div>
  )
}
