import { zodResolver } from '@hookform/resolvers/zod'
import { useState } from 'react'
import { useForm, type UseFormRegisterReturn } from 'react-hook-form'
import { z } from 'zod'

import { updateCurrentUser } from '@/api/auth'
import { ApiError } from '@/api/errors'
import { Button } from '@/components/ui/button'
import { useAuth } from '@/context/AuthContext'
import { usePreferenceChoices } from '@/hooks/usePreferences'
import type { Choice } from '@/types/auth'

import { FormField } from './FormField'

const schema = z.object({
  interests: z.array(z.string()),
  info_types: z.array(z.string()),
  aliases: z.string().trim().max(200, 'At most 200 characters.'),
})
type Preferences = z.infer<typeof schema>

type Props = {
  submitLabel: string
  onSaved?: () => void
}

/** Interests, information types and nicknames. Used by onboarding and profile. */
export function PreferencesForm({ submitLabel, onSaved }: Props) {
  const { user, setUser } = useAuth()
  const profile = user?.student_profile
  const choices = usePreferenceChoices()
  const [saved, setSaved] = useState(false)

  const {
    register,
    handleSubmit,
    setError,
    formState: { errors, isSubmitting },
  } = useForm<Preferences>({
    resolver: zodResolver(schema),
    defaultValues: {
      interests: profile?.interests ?? [],
      info_types: profile?.info_types ?? [],
      aliases: profile?.aliases ?? '',
    },
  })

  async function onSubmit(data: Preferences) {
    setSaved(false)
    try {
      setUser(await updateCurrentUser({ student_profile: data }))
      setSaved(true)
      onSaved?.()
    } catch (error) {
      setError('root', {
        message: error instanceof ApiError ? error.message : 'Something went wrong. Please try again.',
      })
    }
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-6">
      <ChoiceGroup
        legend="What interests you?"
        hint="Opportunities and events about these come first."
        choices={choices.data?.interests}
        field={register('interests')}
      />
      <ChoiceGroup
        legend="What do you want to hear about?"
        hint="Choose none to hear about everything."
        choices={choices.data?.info_types}
        field={register('info_types')}
      />
      <FormField
        label="Nicknames (optional)"
        placeholder="e.g. Abdu, Aziz"
        error={errors.aliases?.message}
        {...register('aliases')}
      />
      <p className="-mt-4 text-xs text-muted-foreground">
        Only used to notice when someone mentions you in a group.
      </p>

      {errors.root && (
        <p role="alert" className="text-sm text-destructive">
          {errors.root.message}
        </p>
      )}
      {saved && !onSaved && (
        <p role="status" className="text-sm text-success">
          Saved.
        </p>
      )}

      <Button type="submit" size="lg" className="w-full" disabled={isSubmitting}>
        {isSubmitting ? 'Saving…' : submitLabel}
      </Button>
    </form>
  )
}

type ChoiceGroupProps = {
  legend: string
  hint: string
  choices: Choice[] | undefined
  field: UseFormRegisterReturn
}

/** A group of tappable choices (checkboxes styled as chips). */
function ChoiceGroup({ legend, hint, choices, field }: ChoiceGroupProps) {
  return (
    <fieldset>
      <legend className="text-sm font-medium">{legend}</legend>
      <p className="text-xs text-muted-foreground">{hint}</p>
      <div className="mt-2 flex flex-wrap gap-2">
        {choices?.map((choice) => (
          <label key={choice.value} className="cursor-pointer">
            <input type="checkbox" value={choice.value} className="peer sr-only" {...field} />
            <span className="inline-flex min-h-10 items-center rounded-full border border-border px-3 text-sm peer-checked:border-primary peer-checked:bg-primary peer-checked:text-primary-foreground peer-focus-visible:ring-2 peer-focus-visible:ring-ring">
              {choice.label}
            </span>
          </label>
        ))}
      </div>
    </fieldset>
  )
}
