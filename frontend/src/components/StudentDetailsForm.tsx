import { zodResolver } from '@hookform/resolvers/zod'
import { useState } from 'react'
import { useForm, useWatch } from 'react-hook-form'
import { z } from 'zod'

import { updateCurrentUser } from '@/api/auth'
import { ApiError } from '@/api/errors'
import { Button } from '@/components/ui/button'
import { useAuth } from '@/context/AuthContext'
import { useIntakes, useProgrammes, useSchools } from '@/hooks/useAcademics'

import { FormField } from './FormField'
import { SelectField } from './SelectField'

// <select> values are strings; empty means "not chosen yet".
const schema = z.object({
  school: z.string().min(1, 'Choose your school.'),
  programme: z.string().min(1, 'Choose your programme.'),
  intake: z.string().min(1, 'Choose your intake.'),
  student_number: z.string().trim().max(32, 'At most 32 characters.'),
})
type StudentDetails = z.infer<typeof schema>

type Props = {
  submitLabel: string
  onSaved?: () => void
}

/** School → programme → intake (+ optional student number). Used by onboarding and profile. */
export function StudentDetailsForm({ submitLabel, onSaved }: Props) {
  const { user, setUser } = useAuth()
  const profile = user?.student_profile
  const [saved, setSaved] = useState(false)

  const {
    register,
    handleSubmit,
    setValue,
    setError,
    control,
    formState: { errors, isSubmitting },
  } = useForm<StudentDetails>({
    resolver: zodResolver(schema),
    defaultValues: {
      school: profile?.school ? String(profile.school) : '',
      programme: profile?.programme ? String(profile.programme) : '',
      intake: profile?.intake ? String(profile.intake) : '',
      student_number: profile?.student_number ?? '',
    },
  })

  const school = useWatch({ control, name: 'school' })
  const schoolId = school ? Number(school) : null
  const schools = useSchools()
  const programmes = useProgrammes(schoolId)
  const intakes = useIntakes()

  async function onSubmit(data: StudentDetails) {
    setSaved(false)
    try {
      const updated = await updateCurrentUser({
        student_profile: {
          school: Number(data.school),
          programme: Number(data.programme),
          intake: Number(data.intake),
          student_number: data.student_number || null,
        },
      })
      setUser(updated)
      setSaved(true)
      onSaved?.()
    } catch (error) {
      // Backend errors arrive as { student_profile: { programme: [...], ... } }.
      const nested = error instanceof ApiError ? error.fields.student_profile : undefined
      const fieldErrors = nested && !Array.isArray(nested) ? (nested as Record<string, string[]>) : {}
      let shown = false
      for (const field of ['school', 'programme', 'intake', 'student_number'] as const) {
        if (fieldErrors[field]?.length) {
          setError(field, { message: fieldErrors[field].join(' ') })
          shown = true
        }
      }
      if (!shown) {
        setError('root', {
          message: error instanceof ApiError ? error.message : 'Something went wrong. Please try again.',
        })
      }
    }
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-4">
      {/* Each dropdown is redrawn (key) once its options load, so a saved choice shows. */}
      <SelectField
        key={`school-${schools.data?.length ?? 0}`}
        label="School"
        error={errors.school?.message}
        {...register('school', {
          // A programme from the previous school would no longer be valid.
          onChange: () => setValue('programme', ''),
        })}
      >
        <option value="">Choose your school…</option>
        {schools.data?.map((school) => (
          <option key={school.id} value={school.id}>
            {school.name}
          </option>
        ))}
      </SelectField>

      <SelectField
        key={`programme-${schoolId}-${programmes.data?.length ?? 0}`}
        label="Programme"
        disabled={schoolId === null}
        error={errors.programme?.message}
        {...register('programme')}
      >
        <option value="">{schoolId === null ? 'Choose a school first' : 'Choose your programme…'}</option>
        {programmes.data?.map((programme) => (
          <option key={programme.id} value={programme.id}>
            {programme.name}
          </option>
        ))}
      </SelectField>

      <SelectField
        key={`intake-${intakes.data?.length ?? 0}`}
        label="Intake"
        error={errors.intake?.message} {...register('intake')}>
        <option value="">Choose your intake…</option>
        {intakes.data?.map((intake) => (
          <option key={intake.id} value={intake.id}>
            {intake.name}
          </option>
        ))}
      </SelectField>

      <FormField
        label="Student number (optional)"
        error={errors.student_number?.message}
        {...register('student_number')}
      />

      {errors.root && (
        <p role="alert" className="text-sm text-destructive">
          {errors.root.message}
        </p>
      )}
      {saved && !onSaved && (
        <p role="status" className="text-sm text-emerald-700">
          Saved.
        </p>
      )}

      <Button type="submit" size="lg" className="w-full" disabled={isSubmitting}>
        {isSubmitting ? 'Saving…' : submitLabel}
      </Button>
    </form>
  )
}
