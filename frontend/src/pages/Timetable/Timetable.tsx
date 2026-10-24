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
import {
  useClassChanges,
  useLeaveSection,
  useMoveSections,
  useMySections,
  useSemesters,
  useToday,
  useWeek,
} from '@/hooks/useTimetable'
import { changeLabel, formatDay, meetingText, nowInMalaysia, shiftDate, todayIsoInMalaysia } from '@/lib/timetable'
import { cn } from '@/lib/utils'
import type { ClassSlot, Section, Semester, SemesterChoice, TimetableDays } from '@/types/timetable'

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
  const [semester, setSemester] = useState<SemesterChoice>('current')
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

      <section aria-labelledby="my-sections" className="space-y-4 rounded-2xl bg-card p-4 md:p-6 dark:ring-1 dark:ring-border">
        <h2 id="my-sections" className="text-lg font-medium">
          My sections
        </h2>
        <MySectionList />

        <div className="space-y-2">
          <h3 className="text-sm font-medium text-muted-foreground">Add classes</h3>
          <SemesterChooser value={semester} onChange={setSemester} />
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
            {panel === 'pick' && (
              <SectionPicker semester={semester} mySectionIds={mySections.data?.map((section) => section.id) ?? []} />
            )}
            {panel === 'add' && <AddClassForm semester={semester} />}
            {panel === 'import' && <TimetableImportBox key={semester} semester={semester} />}
          </AddPanel>
        )}
      </section>
    </div>
  )
}

/** "Tue 26 Oct" from "2026-10-26". */
function shortDate(iso: string): string {
  return new Date(`${iso}T00:00:00Z`).toLocaleDateString('en-GB', {
    weekday: 'short',
    day: 'numeric',
    month: 'short',
    timeZone: 'UTC',
  })
}

/** "now" for a semester that has started, else when it starts. */
function whenText(semester: Semester): string {
  return semester.starts_on <= todayIsoInMalaysia() ? 'now' : `starts ${shortDate(semester.starts_on)}`
}

/** Which semester new classes go to: this one or the next (no dates to type: UniFlow knows them). */
function SemesterChooser({ value, onChange }: { value: SemesterChoice; onChange: (value: SemesterChoice) => void }) {
  const semesters = useSemesters()
  if (!semesters.data?.current) return null
  const options = (
    [
      ['current', semesters.data.current],
      ['next', semesters.data.next],
    ] as const
  ).filter((option): option is readonly [SemesterChoice, Semester] => option[1] !== null)
  return (
    <fieldset>
      <legend className="sr-only">Which semester are these classes for?</legend>
      <p aria-hidden className="mb-2 text-sm">
        Which semester are these classes for?
      </p>
      <div className="flex flex-wrap gap-2">
        {options.map(([choice, semester]) => (
          <label key={choice} className="cursor-pointer">
            <input
              type="radio"
              name="semester"
              value={choice}
              checked={value === choice}
              onChange={() => onChange(choice)}
              className="peer sr-only"
            />
            <span className="inline-flex min-h-11 items-center gap-1.5 rounded-full border border-border px-3.5 text-sm peer-checked:border-primary peer-checked:bg-primary peer-checked:font-medium peer-checked:text-primary-foreground peer-focus-visible:ring-3 peer-focus-visible:ring-ring/50 md:min-h-9">
              {semester.name}
              <span className="font-normal opacity-80">· {whenText(semester)}</span>
            </span>
          </label>
        ))}
      </div>
    </fieldset>
  )
}

/** The open "add classes" tool, with its name, a one-line hint and a close button. */
function AddPanel({ panel, onClose, children }: { panel: Exclude<Panel, 'none'>; onClose: () => void; children: ReactNode }) {
  const { label, hint } = PANELS.find((item) => item.value === panel)!
  return (
    <div className="space-y-4 rounded-xl bg-background p-4 ring-1 ring-border">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="font-medium">{label}</p>
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
    <div className="island flex flex-wrap items-center gap-x-3 gap-y-2 rounded-2xl py-2.5 pr-2.5 pl-4 text-sm">
      <CircleAlert aria-hidden className="size-4 shrink-0 text-primary" />
      <p className="flex-1">{waiting === 1 ? '1 class change to confirm.' : `${waiting} class changes to confirm.`}</p>
      <Button asChild size="sm">
        <a href="#changes">Review</a>
      </Button>
    </div>
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
        <p className="text-sm font-medium tabular-nums">
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
            !week.data.term
              ? 'Use the arrows to see another week, or add your classes below.'
              : week.data.term.starts_on > sunday
                ? `${week.data.term.name} starts on ${shortDate(week.data.term.starts_on)}; your classes show from then. Use the arrows to see that week.`
                : week.data.term.ends_on < monday
                  ? `${week.data.term.name} ended on ${shortDate(week.data.term.ends_on)}. If your classes are for the new semester, move them under My sections.`
                  : `No classes from ${week.data.term.name} this week. Use the arrows to see another week.`
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
            <h2 className={cn('text-sm font-medium', isToday ? 'text-foreground' : 'text-muted-foreground')}>
              {formatDay(day.date)}
            </h2>
            {day.classes.length === 0 ? (
              <p className="text-sm text-muted-foreground">{emptyText}</p>
            ) : (
              <ul className="divide-y divide-border overflow-hidden rounded-2xl bg-card dark:ring-1 dark:ring-border">
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
      <p className={cn('w-24 shrink-0 text-sm font-medium tabular-nums', cancelled && 'text-muted-foreground line-through')}>
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

/** My sections grouped by semester (this one, the next, and one that just ended). */
function MySectionList() {
  const mySections = useMySections()
  if (!mySections.data?.length) return null
  const groups = new Map<number, { semester: Semester; sections: Section[] }>()
  for (const section of mySections.data) {
    const group = groups.get(section.semester.id) ?? { semester: section.semester, sections: [] }
    group.sections.push(section)
    groups.set(section.semester.id, group)
  }
  return (
    <div className="space-y-5">
      {[...groups.values()].map(({ semester, sections }) => (
        <SemesterSections key={semester.id} semester={semester} sections={sections} />
      ))}
    </div>
  )
}

/** One semester's sections; for a semester that has ended, a way to move them to the current one. */
function SemesterSections({ semester, sections }: { semester: Semester; sections: Section[] }) {
  const leave = useLeaveSection()
  const move = useMoveSections()
  const semesters = useSemesters()
  const ended = semester.ends_on < todayIsoInMalaysia()
  const current = semesters.data?.current
  return (
    <section aria-label={semester.name} className="space-y-2">
      <h3 className="flex flex-wrap items-baseline gap-x-2 text-sm font-medium">
        {semester.name}
        <span className="font-normal text-muted-foreground">
          {ended ? `ended ${shortDate(semester.ends_on)}` : whenText(semester)}
        </span>
      </h3>
      {ended && current && current.id !== semester.id && (
        <div className="flex flex-wrap items-center gap-x-3 gap-y-2 rounded-xl bg-muted/60 p-3 text-sm">
          <p className="flex-1">Are these classes for {current.name}? Move them, and they show from {shortDate(current.starts_on)}.</p>
          <Button size="sm" disabled={move.isPending} onClick={() => move.mutate(semester.id)}>
            Move to {current.name}
          </Button>
        </div>
      )}
      <ul className="divide-y divide-border border-y border-border">
      {sections.map((section) => (
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
    </section>
  )
}
