import { CalendarClock } from 'lucide-react'
import { Link } from 'react-router'

import { Badge } from '@/components/ui/badge'
import { useAuth } from '@/context/AuthContext'
import { useHome } from '@/hooks/useFeed'
import { changeLabel, nowInMalaysia } from '@/lib/timetable'
import { cn } from '@/lib/utils'
import type { ClassSlot } from '@/types/timetable'

type Moment = 'past' | 'now' | 'next' | 'later'

/** Where each class sits against the time now: finished, happening, the next one, or later. */
function moments(classes: ClassSlot[], now: string): Moment[] {
  let nextFound = false
  return classes.map((slot) => {
    if (slot.end_time <= now) return 'past'
    if (slot.start_time <= now) return 'now'
    if (!nextFound) {
      nextFound = true
      return 'next'
    }
    return 'later'
  })
}

/**
 * The "Today rail" at the top of For you: today's classes on a timeline, with the class
 * happening now and the next one named in words, confirmed changes shown on the class, and
 * the class changes waiting for an answer (GET feed/home/). Students only: staff have no classes.
 */
export function TodayBox({ className }: { className?: string }) {
  const { user } = useAuth()
  const home = useHome()
  if (user?.role !== 'student' || !home.data) return null

  const { todays_classes: classes, pending_timetable_changes: waiting } = home.data
  const when = moments(classes, nowInMalaysia())

  return (
    <section aria-label="Today" className={cn('rounded-xl bg-card p-4 ring-1 ring-border md:p-5', className)}>
      <div className="flex items-center justify-between gap-2">
        <h2 className="flex items-center gap-2 font-medium">
          <CalendarClock aria-hidden className="size-[1.125rem] text-foreground" />
          Today
        </h2>
        <Link to="/timetable" className="text-sm font-medium text-foreground underline underline-offset-4 hover:decoration-2">
          Timetable
        </Link>
      </div>

      {classes.length === 0 ? (
        <p className="mt-3 text-sm text-muted-foreground">No classes today.</p>
      ) : (
        <ol className="mt-4">
          {classes.map((slot, index) => {
            const cancelled = slot.change?.kind === 'class_cancelled' && slot.change.status === 'confirmed'
            const moment = when[index]
            const last = index === classes.length - 1
            return (
              <li key={`${slot.section_id}-${slot.start_time}`} className="relative flex gap-3 pb-4 last:pb-0">
                {/* The rail: a dot per class, joined by a line; the class happening now is filled. */}
                <span aria-hidden className="relative flex w-3 shrink-0 justify-center pt-1.5">
                  <span
                    className={cn(
                      'z-10 size-3 rounded-full border-2',
                      moment === 'now' ? 'border-primary bg-primary' : 'border-input bg-card',
                      moment === 'past' && 'border-border',
                    )}
                  />
                  {!last && <span className="absolute top-5 bottom-[-0.375rem] w-px bg-border" />}
                </span>
                <div className={cn('min-w-0 flex-1', moment === 'past' && 'opacity-60')}>
                  <div className="flex flex-wrap items-center gap-x-2 gap-y-1">
                    <span className={cn('text-sm font-medium tabular-nums', cancelled && 'text-muted-foreground line-through')}>
                      {slot.start_time}–{slot.end_time}
                    </span>
                    {moment === 'now' && <Badge>Now</Badge>}
                    {moment === 'next' && <Badge variant="secondary">Next</Badge>}
                    {slot.change && (
                      <Badge variant="outline" className={slot.change.status === 'pending' ? 'border-attention-border' : undefined}>
                        {changeLabel(slot.change)}
                      </Badge>
                    )}
                  </div>
                  <p className="mt-0.5 truncate text-sm text-muted-foreground">
                    {slot.course_code}
                    {slot.room && ` · ${slot.room}`}
                  </p>
                </div>
              </li>
            )
          })}
        </ol>
      )}

      {waiting.length > 0 && (
        <p className="mt-4 rounded-lg bg-attention p-3 text-sm text-foreground ring-1 ring-attention-border">
          {waiting.length === 1 ? '1 class change is' : `${waiting.length} class changes are`} waiting for
          you.{' '}
          <Link to="/timetable" className="font-medium text-attention-foreground underline underline-offset-2">
            Confirm or reject
          </Link>
        </p>
      )}
    </section>
  )
}
