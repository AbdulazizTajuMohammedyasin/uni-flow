import { zodResolver } from '@hookform/resolvers/zod'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { z } from 'zod'

import { changePassword } from '@/api/auth'
import { ApiError } from '@/api/errors'
import { Button } from '@/components/ui/button'

import { FormField } from './FormField'

const schema = z
  .object({
    current_password: z.string().min(1, 'Enter your current password.'),
    new_password: z.string().min(8, 'Use at least 8 characters.'),
    re_new_password: z.string().min(1, 'Type your new password again.'),
  })
  .refine((data) => data.new_password === data.re_new_password, {
    path: ['re_new_password'],
    message: 'The passwords do not match.',
  })
type ChangePasswordForm = z.infer<typeof schema>
const FIELDS = ['current_password', 'new_password', 're_new_password'] as const

export function ChangePasswordForm() {
  const [saved, setSaved] = useState(false)
  const {
    register,
    handleSubmit,
    setError,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<ChangePasswordForm>({ resolver: zodResolver(schema) })

  async function onSubmit(data: ChangePasswordForm) {
    setSaved(false)
    try {
      await changePassword(data)
      reset()
      setSaved(true)
    } catch (error) {
      if (!(error instanceof ApiError)) {
        setError('root', { message: 'Something went wrong. Please try again.' })
        return
      }
      let shown = false
      for (const field of FIELDS) {
        if (error.fields[field]?.length) {
          setError(field, { message: error.fields[field].join(' ') })
          shown = true
        }
      }
      if (!shown) setError('root', { message: error.message })
    }
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-4">
      <FormField
        label="Current password"
        type="password"
        autoComplete="current-password"
        error={errors.current_password?.message}
        {...register('current_password')}
      />
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
          {errors.root.message}
        </p>
      )}
      {saved && (
        <p role="status" className="text-sm text-emerald-700">
          Password changed.
        </p>
      )}
      <Button type="submit" disabled={isSubmitting}>
        {isSubmitting ? 'Saving…' : 'Change password'}
      </Button>
    </form>
  )
}
