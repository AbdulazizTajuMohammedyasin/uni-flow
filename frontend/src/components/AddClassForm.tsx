import { zodResolver } from '@hookform/resolvers/zod'
import { useState } from 'react'
import { useFieldArray, useForm } from 'react-hook-form'
import { z } from 'zod'

import { ApiError } from '@/api/errors'
import { Button } from '@/components/ui/button'
import { useAddSection } from '@/hooks/useTimetable'
import type { SemesterChoice } from '@/types/timetable'

import { FormField } from './FormField'
import { SelectField } from './SelectField'

const WEEKDAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

const meetingSchema = z
  .object({
    weekday: z.string(),
    start_time: z.string().min(1, 'Required.'),
    end_time: z.string().min(1, 'Required.'),
    meeting_type: z.enum(['lecture', 'tutorial', 'lab', 'other']),
    room: z.string().trim().max(50),
  })
  .refine((meeting) => meeting.end_time > meeting.start_time, {
    message: 'Must end after it starts.',
    path: ['end_time'],
  })

const schema = z.object({
  course_code: z.string().trim().min(1, 'Enter the course code.').max(20),
  course_name: z.string().trim().min(1, 'Enter the course name.').max(200),
  section: z.string().trim().min(1, 'Enter the section, e.g. A.').max(20),
  meetings: z.array(meetingSchema).min(1),
})
type NewClass = z.infer<typeof schema>

const EMPTY_MEETING = {
  weekday: '0',
  start_time: '',
  end_time: '',
  meeting_type: 'lecture' as const,
  room: '',
}

/** Add a class that is not in UniFlow yet: course, section and its weekly classes. */
export function AddClassForm({ semester = 'current' }: { semester?: SemesterChoice }) {
  const add = useAddSection()
  const [message, setMessage] = useState('')
  const {
    register,
    control,
    handleSubmit,
    reset,
    setError,
    formState: { errors, isSubmitting },
  } = useForm<NewClass>({
    resolver: zodResolver(schema),
    defaultValues: { course_code: '', course_name: '', section: '', meetings: [EMPTY_MEETING] },
  })
  const meetings = useFieldArray({ control, name: 'meetings' })

  async function onSubmit(data: NewClass) {
    setMessage('')
    try {
      const section = await add.mutateAsync({
        ...data,
        semester,
        meetings: data.meetings.map((meeting) => ({
          ...meeting,
          weekday: Number(meeting.weekday),
          building: '',
        })),
      })
      setMessage(`Added ${section.course.code} Section ${section.code} to your timetable.`)
      reset()
    } catch (error) {
      setError('root', {
        message: error instanceof ApiError ? error.message : 'Something went wrong. Please try again.',
      })
    }
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-4">
      <div className="grid gap-3 sm:grid-cols-[1fr_2fr_6rem]">
        <FormField
          label="Course code"
          placeholder="CDE2313"
          error={errors.course_code?.message}
          {...register('course_code')}
        />
        <FormField
          label="Course name"
          placeholder="Data Structures"
          error={errors.course_name?.message}
          {...register('course_name')}
        />
        <FormField
          label="Section"
          placeholder="A"
          error={errors.section?.message}
          {...register('section')}
        />
      </div>

      <fieldset className="space-y-3">
        <legend className="text-sm font-medium">Weekly classes</legend>
        {meetings.fields.map((field, index) => (
          <div
            key={field.id}
            className="grid gap-3 rounded-xl p-3 ring-1 ring-border sm:grid-cols-[1fr_7rem_7rem_1fr_1fr_auto] sm:items-end"
          >
            <SelectField label="Day" {...register(`meetings.${index}.weekday`)}>
              {WEEKDAYS.map((day, value) => (
                <option key={day} value={value}>
                  {day}
                </option>
              ))}
            </SelectField>
            <FormField
              label="Starts"
              type="time"
              error={errors.meetings?.[index]?.start_time?.message}
              {...register(`meetings.${index}.start_time`)}
            />
            <FormField
              label="Ends"
              type="time"
              error={errors.meetings?.[index]?.end_time?.message}
              {...register(`meetings.${index}.end_time`)}
            />
            <SelectField label="Type" {...register(`meetings.${index}.meeting_type`)}>
              <option value="lecture">Lecture</option>
              <option value="tutorial">Tutorial</option>
              <option value="lab">Lab</option>
              <option value="other">Other</option>
            </SelectField>
            <FormField label="Room" {...register(`meetings.${index}.room`)} />
            {meetings.fields.length > 1 && (
              <Button type="button" variant="ghost" size="sm" onClick={() => meetings.remove(index)}>
                Remove
              </Button>
            )}
          </div>
        ))}
        <Button type="button" variant="outline" size="sm" onClick={() => meetings.append(EMPTY_MEETING)}>
          Add another weekly class
        </Button>
      </fieldset>

      {errors.root && (
        <p role="alert" className="text-sm text-destructive">
          {errors.root.message}
        </p>
      )}
      {message && (
        <p role="status" className="text-sm text-success">
          {message}
        </p>
      )}

      <Button type="submit" disabled={isSubmitting}>
        {isSubmitting ? 'Adding…' : 'Add class'}
      </Button>
    </form>
  )
}
