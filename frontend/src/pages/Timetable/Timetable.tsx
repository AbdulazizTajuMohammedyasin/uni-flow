import { ChevronLeft, ChevronRight, CircleAlert, FilePlus2, ListChecks, Plus, X, type LucideIcon } from 'lucide-react'
import { useState, type ReactNode } from 'react'
import { useSearchParams } from 'react-router'

import { AddClassForm } from '@/components/AddClassForm'
import { ClassChanges } from '@/components/ClassChanges'
import { EmptyState } from '@/components/EmptyState'
import { ErrorState } from '@/components/ErrorState'
import { ListSkeleton } from '@/components/ListSkeleton'
import { PageHeader } from '@/components/PageHeader'
import { SectionPicker } from '@/components/SectionPicker'
import { GroupTimetableOffer, TimetableImportBox } from '@/components/TimetableImport'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { WeekGrid } from '@/components/WeekGrid'
import { useMediaQuery } from '@/hooks/useMediaQuery'
import { useClassChanges, useLeaveSection, useMySections, useToday, useWeek } from '@/hooks/useTimetable'
import { changeLabel, formatDay, meetingText, nowInMalaysia, shiftDate, todayIsoInMalaysia } from '@/lib/timetable'
import { cn } from '@/lib/utils'
import type { ClassSlot, TimetableDays } from '@/types/timetable'

type Panel = 'none' | 'import' | 'pick' | 'add'

const PANELS: { value: Exclude<Panel, 'none'>; label: string; hint: string; Icon: LucideIcon }[] = [
  { value: 'import', label: 'Add my timetable', hint: 'UniFlow reads a photo, PDF, Excel file or link', Icon: FilePlus2 },
  { value: 'pick', label: 'Choose sections', hint: "Search this term's sections", Icon: ListChecks },
  { value: 'add', label: 'Add a missing class', hint: 'Not in UniFlow yet? Type it in', Icon: Plus },
]

/**
 * /timetable — my classes today or this week, the changes waiting for my answer, my sections,
 * and adding classes. On laptop screens (1024 px+) the week is a grid like AIU's own timetable
 * (days down, hours across); elsewhere it is a list per day.
 */
export function TimetablePage() {
  const [params, setParams] = useSearchParams()
  const view = params.get('view') === 'week' ? 'week' : 'today'
  const wide = useMediaQuery('(min-width: 1024px)')
  const mySections = useMySections()
  const [panel, setPanel] = useState<Panel>('none')
  const hasSections = (mySections.data?.length ?? 0) > 0

  const show = (next: 'today' | 'week') => setParams(next === 'week' ? { view: 'week' } : {})

  return (
    <div className={cn('space-y-6 md:space-y-8', view === 'week' && wide ? 'max-w-none' : 'max-w-3xl')}>
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

      {mySections.isPending ? (
        <ListSkeleton />
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
        <>
          <ChangesNotice />
          <WeekView
            date={params.get('date') ?? undefined}
            onDate={(date) => setParams({ view: 'week', date })}
            grid={wide}
          />
        </>
      )}

      {/* Changes the AI found: after the classes, so they don't push them off the screen. */}
      {hasSections && (
        <div id="changes" className="scroll-mt-20">
          <ClassChanges />
        </div>
      )}

      <section aria-labelledby="my-sections" className="space-y-4 rounded-xl bg-card p-4 ring-1 ring-border md:p-6">
        <h2 id="my-sections" className="text-lg font-semibold">
          My sections
        </h2>
        <MySectionList />

        <div className="space-y-2">
          <h3 className="text-sm font-medium text-muted-foreground">Add classes</h3>
          <div className="flex flex-wrap gap-2">
            {PANELS.map(({ value, label, Icon }) => (
              <Button
                key={value}
                size="sm"
                variant={panel === value ? 'default' : 'outline'}
                aria-expanded={panel === value}
                onClick={() => setPanel(panel === value ? 'none' : value)}
              >
                <Icon aria-hidden />
                {label}
              </Button>
            ))}
          </div>
        </div>

        {panel !== 'none' && (
          <AddPanel panel={panel} onClose={() => setPanel('none')}>
            {panel === 'pick' && <SectionPicker mySectionIds={mySections.data?.map((section) => section.id) ?? []} />}
            {panel === 'add' && <AddClassForm />}
            {panel === 'import' && <TimetableImportBox />}
          </AddPanel>
        )}
      </section>
    </div>
  )
}

/** The open "add classes" tool, with its name, a one-line hint and a close button. */
function AddPanel({ panel, onClose, children }: { panel: Exclude<Panel, 'none'>; onClose: () => void; children: ReactNode }) {
  const { label, hint } = PANELS.find((item) => item.value === panel)!
  return (
    <div className="space-y-4 rounded-lg bg-background p-4 ring-1 ring-border">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="font-semibold">{label}</p>
          <p className="text-sm text-muted-foreground">{hint}</p>
        </div>
        <Button size="icon-sm" variant="ghost" onClick={onClose} aria-label="Close">
          <X aria-hidden />
        </Button>
      </div>
      {children}
    </div>
  )
}

/** In the week view the changes list sits far below: a short note at the top points to it. */
function ChangesNotice() {
  const changes = useClassChanges()
  const waiting = changes.data?.filter((change) => change.my_status === 'pending').length ?? 0
  if (waiting === 0) return null
  return (
    <p className="flex flex-wrap items-center gap-2 rounded-xl bg-attention p-3 text-sm text-foreground ring-1 ring-attention-border">
      <CircleAlert aria-hidden className="size-4 shrink-0 text-attention-foreground" />
      {waiting === 1 ? '1 class change to confirm.' : `${waiting} class changes to confirm.`}
      <a href="#changes" className="font-semibold text-attention-foreground underline underline-offset-2">
        Review
      </a>
    </p>
  )
}

function TodayView() {
  const today = useToday()
  if (today.isPending) return <ListSkeleton />
  if (today.isError) return <ErrorState title="Could not load today's classes" />
  return <DayList days={today.data.days} emptyText="No classes today." />
}

function WeekView({ date, onDate, grid }: { date?: string; onDate: (date: string) => void; grid: boolean }) {
  const week = useWeek(date)
  if (week.isPending) return <ListSkeleton />
  if (week.isError) return <ErrorState title="Could not load this week" />
  const monday = week.data.days[0].date
  const sunday = week.data.days[week.data.days.length - 1].date
  const range = (day: string) =>
    new Date(`${day}T00:00:00Z`).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', timeZone: 'UTC' })
  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between gap-2">
        <Button size="sm" variant="ghost" onClick={() => onDate(shiftDate(monday, -7))}>
          <ChevronLeft aria-hidden />
          <span className="sr-only md:not-sr-only">Previous week</span>
        </Button>
        <p className="text-sm font-semibold tabular-nums">
          {range(monday)} – {range(sunday)}
        </p>
        <Button size="sm" variant="ghost" onClick={() => onDate(shiftDate(monday, 7))}>
          <span className="sr-only md:not-sr-only">Next week</span>
          <ChevronRight aria-hidden />
        </Button>
      </div>
      {week.data.days.every((day) => day.classes.length === 0) ? (
        // A whole empty week (a break, or a term that ended): say so instead of an empty table.
        <EmptyState
          title="No classes this week"
          description={
            week.data.term
              ? `Your classes are from ${week.data.term.name}. Use the arrows to see another week, or if a new semester has started, add your new classes below.`
              : 'Use the arrows to see another week, or add your classes below.'
          }
        />
      ) : grid ? (
        <WeekGrid days={week.data.days} today={todayIsoInMalaysia()} />
      ) : (
        <DayList days={week.data.days} emptyText="No classes." />
      )}
    </div>
  )
}

/** One day per block: its date, then its classes as rows (or one quiet line when free). */
function DayList({ days, emptyText }: { days: TimetableDays['days']; emptyText: string }) {
  const todayIso = todayIsoInMalaysia()
  const now = nowInMalaysia()
  return (
    <div className="space-y-5">
      {days.map((day) => {
        const isToday = day.date === todayIso
        const nextIndex = isToday ? day.classes.findIndex((slot) => slot.start_time > now) : -1
        return (
          <section key={day.date} aria-label={formatDay(day.date)} className="space-y-2">
            <h2 className={cn('text-sm font-semibold', isToday ? 'text-foreground' : 'text-muted-foreground')}>
              {formatDay(day.date)}
            </h2>
            {day.classes.length === 0 ? (
              <p className="text-sm text-muted-foreground">{emptyText}</p>
            ) : (
              <ul className="divide-y divide-border overflow-hidden rounded-xl bg-card ring-1 ring-border">
                {day.classes.map((slot, index) => (
                  <ClassRow
                    key={`${slot.section_id}-${slot.start_time}`}
                    slot={slot}
                    moment={
                      !isToday
                        ? undefined
                        : slot.start_time <= now && now < slot.end_time
                          ? 'Now'
                          : index === nextIndex
                            ? 'Next'
                            : undefined
                    }
                    past={isToday && slot.end_time <= now}
                  />
                ))}
              </ul>
            )}
          </section>
        )
      })}
    </div>
  )
}

function ClassRow({ slot, moment, past }: { slot: ClassSlot; moment?: 'Now' | 'Next'; past: boolean }) {
  const place = [slot.building, slot.room].filter(Boolean).join(' ')
  const cancelled = slot.change?.kind === 'class_cancelled' && slot.change.status === 'confirmed'
  return (
    <li className={cn('flex gap-4 px-4 py-3.5', moment === 'Now' && 'bg-accent/60', past && 'opacity-60')}>
      <p className={cn('w-24 shrink-0 text-sm font-semibold tabular-nums', cancelled && 'text-muted-foreground line-through')}>
        {slot.start_time}–{slot.end_time}
      </p>
      <div className="min-w-0 flex-1 space-y-0.5">
        <p className="flex flex-wrap items-center gap-x-2 gap-y-1 font-medium">
          {slot.course_code} · Section {slot.section_code}
          {moment && <Badge variant={moment === 'Now' ? 'default' : 'secondary'}>{moment}</Badge>}
          {slot.change && (
            <Badge
              variant={slot.change.status === 'pending' ? 'outline' : 'secondary'}
              className={slot.change.status === 'pending' ? 'border-attention-border' : undefined}
            >
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
    <ul className="divide-y divide-border border-y border-border">
      {mySections.data.map((section) => (
        <li key={section.id} className="flex items-center justify-between gap-3 py-3">
          <div className="min-w-0">
            <p className="font-medium">
              {section.course.code} · Section {section.code}
            </p>
            <p className="truncate text-sm text-muted-foreground">{section.course.name}</p>
            <p className="truncate text-xs text-muted-foreground">{section.meetings.map(meetingText).join(', ')}</p>
          </div>
          <Button
            size="sm"
            variant="ghost"
            className="shrink-0 text-muted-foreground hover:text-destructive"
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
