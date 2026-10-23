import { zodResolver } from '@hookform/resolvers/zod'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { CircleCheck } from 'lucide-react'
import { Link, useParams } from 'react-router'
import { z } from 'zod'

import { confirmPasswordReset } from '@/api/auth'
import { ApiError } from '@/api/errors'
import { FormField } from '@/components/FormField'
import { ResultIcon } from '@/components/ResultIcon'
import { Button } from '@/components/ui/button'

const schema = z
  .object({
    new_password: z.string().min(8, 'Use at least 8 characters.'),
    re_new_password: z.string().min(1, 'Type your new password again.'),
  })
  .refine((data) => data.new_password === data.re_new_password, {
    path: ['re_new_password'],
    message: 'The passwords do not match.',
  })
type ResetForm = z.infer<typeof schema>

/** Opened from the reset email: /reset-password/:uid/:token */
export function ResetPasswordPage() {
  const { uid = '', token = '' } = useParams()
  const [done, setDone] = useState(false)
  const {
    register,
    handleSubmit,
    setError,
    formState: { errors, isSubmitting },
  } = useForm<ResetForm>({ resolver: zodResolver(schema) })

  async function onSubmit(data: ResetForm) {
    try {
      await confirmPasswordReset({ uid, token, ...data })
      setDone(true)
    } catch (error) {
      if (!(error instanceof ApiError)) {
        setError('root', { message: 'Something went wrong. Please try again.' })
        return
      }
      const passwordMessages = error.fields.new_password
      if (passwordMessages?.length) {
        setError('new_password', { message: passwordMessages.join(' ') })
      } else {
        // uid/token problems: the link is invalid, expired or already used.
        setError('root', {
          message: 'This reset link is invalid or has already been used. Please request a new one.',
        })
      }
    }
  }

  if (done) {
    return (
      <div className="text-center">
        <ResultIcon icon={CircleCheck} tone="success" />
        <h1 className="text-2xl font-medium tracking-tight">Password changed</h1>
        <p className="mt-3 text-sm text-muted-foreground">You can now log in with your new password.</p>
        <Button asChild size="lg" className="mt-6 w-full">
          <Link to="/login">Log in</Link>
        </Button>
      </div>
    )
  }

  return (
    <div>
      <h1 className="text-2xl font-medium tracking-tight">Choose a new password</h1>

      <form onSubmit={handleSubmit(onSubmit)} noValidate className="mt-6 space-y-4">
        <FormField
          label="New password"
          type="password"
          autoComplete="new-password"
          error={errors.new_password?.message}
          {...register('new_password')}
        />
        <FormField
          label="Confirm new password"
          type="password"
          autoComplete="new-password"
          error={errors.re_new_password?.message}
          {...register('re_new_password')}
        />
        {errors.root && (
          <p role="alert" className="text-sm text-destructive">
            {errors.root.message}{' '}
            <Link to="/forgot-password" className="font-medium underline">
              Request a new link
            </Link>
          </p>
        )}
        <Button type="submit" size="lg" className="w-full" disabled={isSubmitting}>
          {isSubmitting ? 'Saving…' : 'Save new password'}
        </Button>
      </form>
    </div>
  )
}
