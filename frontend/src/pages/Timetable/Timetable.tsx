import { useState } from 'react'
import { useSearchParams } from 'react-router'

import { AddClassForm } from '@/components/AddClassForm'
import { ClassChanges } from '@/components/ClassChanges'
import { EmptyState } from '@/components/EmptyState'
import { ErrorState } from '@/components/ErrorState'
import { PageHeader } from '@/components/PageHeader'
import { PageLoading } from '@/components/PageLoading'
import { SectionPicker } from '@/components/SectionPicker'
import { GroupTimetableOffer, TimetableImportBox } from '@/components/TimetableImport'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { useLeaveSection, useMySections, useToday, useWeek } from '@/hooks/useTimetable'
import { changeLabel, formatDay, meetingText, shiftDate } from '@/lib/timetable'
import type { ClassSlot, TimetableDays } from '@/types/timetable'

/** /timetable — my classes today or this week, my sections, and adding classes. */
export function TimetablePage() {
  const [params, setParams] = useSearchParams()
  const view = params.get('view') === 'week' ? 'week' : 'today'
  const mySections = useMySections()
  const [panel, setPanel] = useState<'none' | 'import' | 'pick' | 'add'>('none')
  const hasSections = (mySections.data?.length ?? 0) > 0

  const show = (next: 'today' | 'week') => setParams(next === 'week' ? { view: 'week' } : {})

  return (
    <div className="max-w-3xl space-y-6">
      <PageHeader
        title="Timetable"
        actions={
          <div role="group" aria-label="View" className="flex gap-1 rounded-lg bg-muted p-1">
            <Button size="sm" variant={view === 'today' ? 'default' : 'ghost'} aria-pressed={view === 'today'} onClick={() => show('today')}>
              Today
            </Button>
            <Button size="sm" variant={view === 'week' ? 'default' : 'ghost'} aria-pressed={view === 'week'} onClick={() => show('week')}>
              This week
            </Button>
          </div>
        }
      />

      <GroupTimetableOffer />
      {hasSections && <ClassChanges />}

      {mySections.isPending ? (
        <PageLoading />
      ) : !hasSections ? (
        <EmptyState
          title="You haven't added your classes yet"
          description="Upload your timetable and UniFlow reads it for you, or choose your sections yourself."
          action={
            <div className="flex flex-wrap justify-center gap-2">
              <Button onClick={() => setPanel('import')}>Add my timetable</Button>
              <Button variant="outline" onClick={() => setPanel('pick')}>
                Choose sections
              </Button>
            </div>
          }
        />
      ) : view === 'today' ? (
        <TodayView />
      ) : (
        <WeekView date={params.get('date') ?? undefined} onDate={(date) => setParams({ view: 'week', date })} />
      )}

      <section className="space-y-3 rounded-2xl bg-card p-6 shadow-sm ring-1 ring-border">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <h2 className="text-lg font-semibold">My sections</h2>
          <div className="flex flex-wrap gap-2">
            <Button size="sm" variant={panel === 'import' ? 'default' : 'outline'} onClick={() => setPanel(panel === 'import' ? 'none' : 'import')}>
              Add my timetable
            </Button>
            <Button size="sm" variant={panel === 'pick' ? 'default' : 'outline'} onClick={() => setPanel(panel === 'pick' ? 'none' : 'pick')}>
              Choose sections
            </Button>
            <Button size="sm" variant={panel === 'add' ? 'default' : 'outline'} onClick={() => setPanel(panel === 'add' ? 'none' : 'add')}>
              Add a missing class
            </Button>
          </div>
        </div>
        <MySectionList />
        {panel === 'pick' && (
          <SectionPicker mySectionIds={mySections.data?.map((section) => section.id) ?? []} />
        )}
        {panel === 'add' && <AddClassForm />}
        {panel === 'import' && <TimetableImportBox />}
      </section>
    </div>
  )
}

function TodayView() {
  const today = useToday()
  if (today.isPending) return <PageLoading />
  if (today.isError) return <ErrorState title="Could not load today's classes" />
  return <DayList days={today.data.days} emptyText="No classes today." />
}

function WeekView({ date, onDate }: { date?: string; onDate: (date: string) => void }) {
  const week = useWeek(date)
  if (week.isPending) return <PageLoading />
  if (week.isError) return <ErrorState title="Could not load this week" />
  const monday = week.data.days[0].date
  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <Button size="sm" variant="ghost" onClick={() => onDate(shiftDate(monday, -7))}>
          ← Previous week
        </Button>
        <Button size="sm" variant="ghost" onClick={() => onDate(shiftDate(monday, 7))}>
          Next week →
        </Button>
      </div>
      <DayList days={week.data.days} emptyText="No classes." />
    </div>
  )
}

function DayList({ days, emptyText }: { days: TimetableDays['days']; emptyText: string }) {
  return (
    <div className="space-y-4">
      {days.map((day) => (
        <section key={day.date} aria-label={formatDay(day.date)}>
          <h2 className="text-sm font-semibold text-muted-foreground">{formatDay(day.date)}</h2>
          {day.classes.length === 0 ? (
            <p className="mt-1 text-sm text-muted-foreground">{emptyText}</p>
          ) : (
            <ul className="mt-2 space-y-2">
              {day.classes.map((slot) => (
                <ClassCard key={`${slot.section_id}-${slot.start_time}`} slot={slot} />
              ))}
            </ul>
          )}
        </section>
      ))}
    </div>
  )
}

function ClassCard({ slot }: { slot: ClassSlot }) {
  const place = [slot.building, slot.room].filter(Boolean).join(' ')
  const cancelled = slot.change?.kind === 'class_cancelled' && slot.change.status === 'confirmed'
  return (
    <li className="flex gap-4 rounded-xl bg-card p-3 shadow-sm ring-1 ring-border">
      <p className={`w-24 shrink-0 text-sm font-semibold tabular-nums ${cancelled ? 'text-muted-foreground line-through' : ''}`}>
        {slot.start_time}–{slot.end_time}
      </p>
      <div className="min-w-0">
        <p className="flex flex-wrap items-center gap-2 font-medium">
          {slot.course_code} · Section {slot.section_code}
          {slot.change && (
            <Badge variant={slot.change.status === 'pending' ? 'outline' : 'secondary'}>
              {changeLabel(slot.change)}
            </Badge>
          )}
        </p>
        <p className="truncate text-sm text-muted-foreground">
          {slot.course_name}
          {place && ` · ${place}`}
          {slot.meeting_type !== 'lecture' && ` · ${slot.meeting_type}`}
        </p>
      </div>
    </li>
  )
}

function MySectionList() {
  const mySections = useMySections()
  const leave = useLeaveSection()
  if (!mySections.data?.length) return null
  return (
    <ul className="divide-y divide-border">
      {mySections.data.map((section) => (
        <li key={section.id} className="flex items-center justify-between gap-3 py-2">
          <div className="min-w-0">
            <p className="font-medium">
              {section.course.code} · Section {section.code}
            </p>
            <p className="truncate text-xs text-muted-foreground">
              {section.meetings.map(meetingText).join(', ')}
            </p>
          </div>
          <Button
            size="sm"
            variant="ghost"
            disabled={leave.isPending}
            onClick={() => leave.mutate(section.id)}
            aria-label={`Remove ${section.course.code} Section ${section.code}`}
          >
            Remove
          </Button>
        </li>
      ))}
    </ul>
  )
}
