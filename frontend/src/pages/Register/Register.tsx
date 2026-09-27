import { zodResolver } from '@hookform/resolvers/zod'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { Link, Navigate } from 'react-router'
import { z } from 'zod'

import { register as registerAccount } from '@/api/auth'
import { ApiError } from '@/api/errors'
import { FormField } from '@/components/FormField'
import { Button } from '@/components/ui/button'
import { useAuth } from '@/context/AuthContext'

const STUDENT_DOMAIN = '@student.aiu.edu.my'

const schema = z
  .object({
    full_name: z.string().trim().min(2, 'Enter your full name.'),
    email: z
      .email('Enter a valid email address.')
      .refine((email) => email.toLowerCase().endsWith(STUDENT_DOMAIN), {
        message: `Use your AIU student email (${STUDENT_DOMAIN}).`,
      }),
    password: z.string().min(8, 'Use at least 8 characters.'),
    re_password: z.string().min(1, 'Type your password again.'),
  })
  .refine((data) => data.password === data.re_password, {
    path: ['re_password'],
    message: 'The passwords do not match.',
  })
type RegisterForm = z.infer<typeof schema>
const FIELDS = ['full_name', 'email', 'password', 're_password'] as const

export function RegisterPage() {
  const { user } = useAuth()
  const [registeredEmail, setRegisteredEmail] = useState<string | null>(null)

  const {
    register,
    handleSubmit,
    setError,
    formState: { errors, isSubmitting },
  } = useForm<RegisterForm>({ resolver: zodResolver(schema) })

  if (user) {
    return <Navigate to="/" replace />
  }

  async function onSubmit(data: RegisterForm) {
    try {
      await registerAccount(data)
      setRegisteredEmail(data.email)
    } catch (error) {
      if (!(error instanceof ApiError)) {
        setError('root', { message: 'Something went wrong. Please try again.' })
        return
      }
      // Show the backend's messages under the matching field (e.g. "already registered").
      let shown = false
      for (const field of FIELDS) {
        const messages = error.fields[field]
        if (messages?.length) {
          setError(field, { message: messages.join(' ') })
          shown = true
        }
      }
      const general = error.fields.non_field_errors?.join(' ')
      if (general || !shown) {
        setError('root', { message: general ?? error.message })
      }
    }
  }

  if (registeredEmail) {
    return (
      <div className="text-center">
        <h1 className="text-2xl font-bold tracking-tight">Check your email</h1>
        <p className="mt-3 text-sm text-muted-foreground">
          We sent an activation link to <span className="font-medium">{registeredEmail}</span>.
          Open it to activate your account, then log in.
        </p>
        <Button asChild size="lg" className="mt-6 w-full">
          <Link to="/login">Go to log in</Link>
        </Button>
      </div>
    )
  }

  return (
    <div>
      <h1 className="text-2xl font-bold tracking-tight">Create your account</h1>
      <p className="mt-1 text-sm text-muted-foreground">For AIU students ({STUDENT_DOMAIN}).</p>

      <form onSubmit={handleSubmit(onSubmit)} noValidate className="mt-6 space-y-4">
        <FormField
          label="Full name"
          autoComplete="name"
          error={errors.full_name?.message}
          {...register('full_name')}
        />
        <FormField
          label="Student email"
          type="email"
          autoComplete="email"
          placeholder={`name${STUDENT_DOMAIN}`}
          error={errors.email?.message}
          {...register('email')}
        />
        <FormField
          label="Password"
          type="password"
          autoComplete="new-password"
          error={errors.password?.message}
          {...register('password')}
        />
        <FormField
          label="Confirm password"
          type="password"
          autoComplete="new-password"
          error={errors.re_password?.message}
          {...register('re_password')}
        />

        {errors.root && (
          <p role="alert" className="text-sm text-destructive">
            {errors.root.message}
          </p>
        )}

        <Button type="submit" size="lg" className="w-full" disabled={isSubmitting}>
          {isSubmitting ? 'Creating account…' : 'Create account'}
        </Button>
      </form>

      <p className="mt-6 text-center text-sm text-muted-foreground">
        Already have an account?{' '}
        <Link to="/login" className="font-medium text-primary hover:underline">
          Log in
        </Link>
      </p>
    </div>
  )
}
