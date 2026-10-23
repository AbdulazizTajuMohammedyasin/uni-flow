import type { CSSProperties } from 'react'

import { changeLabel, nowInMalaysia } from '@/lib/timetable'
import { cn } from '@/lib/utils'
import type { ClassSlot, TimetableDays } from '@/types/timetable'

type Day = TimetableDays['days'][number]

/** AIU's timetable runs in one-hour slots from 8:30 to 22:30. */
const DAY_START = 8 * 60 + 30
const DAY_END = 22 * 60 + 30

/** "14:30" -> 870 (minutes after midnight). */
function minutes(time: string): number {
  const [hours, mins] = time.split(':').map(Number)
  return hours * 60 + mins
}

/** "870" -> "14:30" */
function clock(total: number): string {
  return `${String(Math.floor(total / 60)).padStart(2, '0')}:${String(total % 60).padStart(2, '0')}`
}

/** Classes that overlap go side by side in "lanes" (stacked rows inside the day). */
function lanes(classes: ClassSlot[]): { slot: ClassSlot; lane: number }[] {
  const ends: number[] = []
  return [...classes]
    .sort((a, b) => a.start_time.localeCompare(b.start_time))
    .map((slot) => {
      let lane = ends.findIndex((end) => end <= minutes(slot.start_time))
      if (lane === -1) lane = ends.length
      ends[lane] = minutes(slot.end_time)
      return { slot, lane }
    })
}

/**
 * "This week" on wide screens, laid out like AIU's own timetable: days down the side, one-hour
 * columns across (8:30 to 22:30, widened if a class falls outside), each class a block over its
 * hours. Today's row is marked, with a line at the current time.
 */
export function WeekGrid({ days, today }: { days: Day[]; today: string }) {
  const all = days.flatMap((day) => day.classes)
  // Whole hours on AIU's :30 grid, widened to fit every class.
  const first = Math.min(DAY_START, ...all.map((slot) => minutes(slot.start_time)))
  const last = Math.max(DAY_END, ...all.map((slot) => minutes(slot.end_time)))
  const start = DAY_START - Math.ceil((DAY_START - first) / 60) * 60
  const end = DAY_END + Math.ceil((last - DAY_END) / 60) * 60
  const span = end - start
  const hours = Array.from({ length: span / 60 }, (_, index) => start + index * 60)
  const at = (time: number) => `${((time - start) / span) * 100}%`
  const now = minutes(nowInMalaysia())

  return (
    <div className="overflow-x-auto rounded-2xl bg-card dark:ring-1 dark:ring-border">
      <table className="w-full min-w-[46rem] table-fixed border-collapse text-sm">
        <caption className="sr-only">Classes this week, by day and time</caption>
        <colgroup>
          <col className="w-20" />
          <col />
        </colgroup>
        <thead>
          <tr className="border-b border-border">
            <th scope="col" className="px-3 py-2 text-left text-xs font-medium text-muted-foreground">
              Day
            </th>
            <th scope="col" className="p-0">
              <span className="sr-only">Time</span>
              <div aria-hidden className="flex">
                {hours.map((hour) => (
                  <span
                    key={hour}
                    className="flex-1 border-l border-border px-1.5 py-2 text-left text-xs font-medium text-muted-foreground tabular-nums"
                  >
                    {clock(hour)}
                  </span>
                ))}
              </div>
            </th>
          </tr>
        </thead>
        <tbody>
          {days.map((day) => {
            const isToday = day.date === today
            const placed = lanes(day.classes)
            const laneCount = Math.max(1, ...placed.map((item) => item.lane + 1))
            const date = new Date(`${day.date}T00:00:00Z`)
            return (
              <tr key={day.date} className="border-b border-border last:border-b-0">
                <th
                  scope="row"
                  className="px-3 py-2.5 text-left align-top"
                >
                  <span className="block font-medium">
                    {date.toLocaleDateString('en-GB', { weekday: 'short', timeZone: 'UTC' })}
                  </span>
                  <span
                    className={cn(
                      'block w-fit text-xs',
                      isToday ? 'mt-0.5 rounded-full bg-primary px-2 py-0.5 font-medium text-primary-foreground' : 'text-muted-foreground',
                    )}
                  >
                    {isToday ? 'Today' : date.toLocaleDateString('en-GB', { day: 'numeric', month: 'short', timeZone: 'UTC' })}
                  </span>
                </th>
                <td className="relative p-0" style={{ height: `${Math.max(6.5, laneCount * 5)}rem` }}>
                  {/* Hour lines */}
                  <div aria-hidden className="absolute inset-0 flex">
                    {hours.map((hour) => (
                      <span key={hour} className="flex-1 border-l border-border/70" />
                    ))}
                  </div>
                  {isToday && now >= start && now <= end && (
                    <span aria-hidden className="absolute inset-y-0 z-0 w-0.5 bg-foreground dark:bg-primary" style={{ left: at(now) }} />
                  )}
                  {day.classes.length === 0 && <span className="sr-only">No classes</span>}
                  <ul>
                    {placed.map(({ slot, lane }) => (
                      <ClassBlock
                        key={`${slot.section_id}-${slot.start_time}`}
                        slot={slot}
                        now={isToday && minutes(slot.start_time) <= now && now < minutes(slot.end_time)}
                        style={{
                          left: at(minutes(slot.start_time)),
                          width: `calc(${at(minutes(slot.end_time))} - ${at(minutes(slot.start_time))})`,
                          top: `calc(${(lane / laneCount) * 100}% + 0.25rem)`,
                          height: `calc(${100 / laneCount}% - 0.5rem)`,
                        }}
                      />
                    ))}
                  </ul>
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}

function ClassBlock({ slot, style, now }: { slot: ClassSlot; style: CSSProperties; now: boolean }) {
  const cancelled = slot.change?.kind === 'class_cancelled' && slot.change.status === 'confirmed'
  const pending = slot.change?.status === 'pending'
  const place = [slot.building, slot.room].filter(Boolean).join(' ')
  return (
    <li
      style={style}
      className={cn(
        'absolute z-10 mx-0.5 overflow-hidden rounded-lg px-2 py-1.5 text-xs leading-[1.35] ring-1',
        cancelled
          ? 'bg-muted text-muted-foreground ring-border'
          : now
            ? 'bg-primary text-primary-foreground ring-primary'
            : 'bg-background text-foreground ring-border dark:bg-muted',
        // A change waiting for an answer: a dashed edge (the label below says which change).
        pending && 'ring-0 outline-[1.5px] -outline-offset-[1.5px] outline-input outline-dashed',
      )}
      title={`${slot.course_code} ${slot.course_name}, section ${slot.section_code}, ${slot.start_time}–${slot.end_time}${place ? `, ${place}` : ''}${slot.change ? ` (${changeLabel(slot.change)})` : ''}`}
    >
      <span className={cn('block truncate font-medium', cancelled && 'line-through')}>
        {slot.course_code} · {slot.section_code}
      </span>
      <span className="block truncate">{slot.course_name}</span>
      <span className="block truncate tabular-nums">
        {slot.start_time}–{slot.end_time}
      </span>
      {place && <span className="block truncate">{place}</span>}
      {now && (
        <span className="mt-1 block w-fit rounded-full bg-primary-foreground px-1.5 font-medium text-primary">Now</span>
      )}
      {slot.change && (
        <span className="mt-1 block max-w-full truncate rounded-full bg-card px-1.5 font-medium text-foreground ring-1 ring-input">
          {changeLabel(slot.change)}
        </span>
      )}
    </li>
  )
}
