import { zodResolver } from '@hookform/resolvers/zod'
import { useForm } from 'react-hook-form'
import { Link, Navigate, useNavigate, useSearchParams } from 'react-router'
import { z } from 'zod'

import { ApiError } from '@/api/errors'
import { FormField } from '@/components/FormField'
import { Button } from '@/components/ui/button'
import { useAuth } from '@/context/AuthContext'

const schema = z.object({
  email: z.email('Enter a valid email address.'),
  password: z.string().min(1, 'Enter your password.'),
})
type LoginForm = z.infer<typeof schema>

/** Only follow ?next= to pages inside UniFlow (never to another website). */
function safeNext(next: string | null): string {
  return next && next.startsWith('/') && !next.startsWith('//') ? next : '/'
}

export function LoginPage() {
  const { user, login } = useAuth()
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const next = safeNext(searchParams.get('next'))

  const {
    register,
    handleSubmit,
    setError,
    formState: { errors, isSubmitting },
  } = useForm<LoginForm>({ resolver: zodResolver(schema) })

  if (user) {
    return <Navigate to={next} replace />
  }

  async function onSubmit(data: LoginForm) {
    try {
      await login(data)
      navigate(next, { replace: true })
    } catch (error) {
      const message =
        error instanceof ApiError && error.status === 401
          ? 'Wrong email or password. If you just registered, open the activation link in your email first.'
          : error instanceof ApiError
            ? error.message
            : 'Something went wrong. Please try again.'
      setError('root', { message })
    }
  }

  return (
    <div>
      <h1 className="text-[1.75rem] leading-tight font-medium tracking-[-0.025em] sm:text-[2rem]">Log in</h1>
      <p className="mt-1 text-sm text-muted-foreground">Use your AIU student email.</p>

      <form onSubmit={handleSubmit(onSubmit)} noValidate className="mt-6 space-y-4">
        <FormField
          label="Email"
          type="email"
          autoComplete="email"
          placeholder="name@student.aiu.edu.my"
          error={errors.email?.message}
          {...register('email')}
        />
        <FormField
          label="Password"
          type="password"
          autoComplete="current-password"
          error={errors.password?.message}
          {...register('password')}
        />
        <div className="text-right text-sm">
          <Link to="/forgot-password" className="font-medium text-foreground underline underline-offset-4 hover:decoration-2">
            Forgot password?
          </Link>
        </div>

        {errors.root && (
          <p role="alert" className="text-sm text-destructive">
            {errors.root.message}
          </p>
        )}

        <Button type="submit" size="lg" className="w-full" disabled={isSubmitting}>
          {isSubmitting ? 'Logging in…' : 'Log in'}
        </Button>
      </form>

      <p className="mt-6 text-center text-sm text-muted-foreground">
        New to UniFlow?{' '}
        <Link to="/register" className="font-medium text-foreground underline underline-offset-4 hover:decoration-2">
          Create an account
        </Link>
      </p>
    </div>
  )
}
