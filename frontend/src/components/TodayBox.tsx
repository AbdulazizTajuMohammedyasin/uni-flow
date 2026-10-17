import { Link } from 'react-router'

import { Badge } from '@/components/ui/badge'
import { useAuth } from '@/context/AuthContext'
import { useHome } from '@/hooks/useFeed'
import { changeLabel } from '@/lib/timetable'

/** Top of "For you": my classes today (with confirmed changes) and class changes waiting
 * for my answer (GET feed/home/). Students only: staff have no classes. */
export function TodayBox() {
  const { user } = useAuth()
  const home = useHome()
  if (user?.role !== 'student' || !home.data) return null

  const { todays_classes: classes, pending_timetable_changes: waiting } = home.data
  return (
    <section aria-label="Today" className="space-y-3 rounded-2xl bg-card p-4 shadow-sm ring-1 ring-border">
      <div className="flex items-center justify-between gap-2">
        <h2 className="font-semibold">Today</h2>
        <Link to="/timetable" className="text-sm text-primary hover:underline">
          Timetable
        </Link>
      </div>
      {classes.length === 0 ? (
        <p className="text-sm text-muted-foreground">No classes today.</p>
      ) : (
        <ul className="space-y-1">
          {classes.map((slot) => {
            const cancelled = slot.change?.kind === 'class_cancelled' && slot.change.status === 'confirmed'
            return (
              <li key={`${slot.section_id}-${slot.start_time}`} className="flex flex-wrap items-center gap-2 text-sm">
                <span className={`w-24 font-semibold tabular-nums ${cancelled ? 'text-muted-foreground line-through' : ''}`}>
                  {slot.start_time}–{slot.end_time}
                </span>
                <span>
                  {slot.course_code}
                  {slot.room && ` · ${slot.room}`}
                </span>
                {slot.change && <Badge variant="outline">{changeLabel(slot.change)}</Badge>}
              </li>
            )
          })}
        </ul>
      )}
      {waiting.length > 0 && (
        <p className="rounded-lg bg-attention p-2 text-sm ring-1 ring-attention-border">
          {waiting.length === 1 ? '1 class change is' : `${waiting.length} class changes are`} waiting for
          you.{' '}
          <Link to="/timetable" className="font-medium text-primary underline">
            Confirm or reject
          </Link>
        </p>
      )}
    </section>
  )
}
