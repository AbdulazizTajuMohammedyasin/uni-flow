import { CircleAlert } from 'lucide-react'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { useAnswerChange, useClassChanges } from '@/hooks/useTimetable'
import { changeText, formatDay } from '@/lib/timetable'
import type { ClassChange } from '@/types/timetable'

/** Changes the AI found in group messages that I haven't answered yet. My timetable
 * changes only if I confirm (and only mine, not my classmates'). A moved class or room change
 * can be confirmed for that week only or every week; those for every week are listed after. */
export function ClassChanges() {
  const changes = useClassChanges()
  const waiting = changes.data?.filter((change) => change.my_status === 'pending') ?? []
  const everyWeek = changes.data?.filter((change) => change.my_status === 'confirmed' && change.every_week) ?? []

  return (
    <>
      {waiting.length > 0 && <WaitingChanges waiting={waiting} />}
      {everyWeek.length > 0 && <EveryWeekChanges changes={everyWeek} />}
    </>
  )
}

function WaitingChanges({ waiting }: { waiting: ClassChange[] }) {
  return (
    <section aria-label="Changes to confirm" className="island space-y-4 rounded-2xl p-4 md:p-5">
      <div>
        <h2 className="flex items-center gap-2 text-lg font-medium">
          <CircleAlert aria-hidden className="size-[1.125rem] text-primary" />
          {waiting.length === 1 ? 'A class may have changed' : `${waiting.length} classes may have changed`}
        </h2>
        <p className="mt-0.5 text-sm text-island-muted">
          UniFlow found this in a group message. Only your own timetable changes, and only if you confirm.
        </p>
      </div>
      <ul className="divide-y divide-border overflow-hidden rounded-xl bg-card text-card-foreground">
        {waiting.map((change) => (
          <ChangeCard key={change.id} change={change} />
        ))}
      </ul>
    </section>
  )
}

/** Changes I confirmed for every week: I can keep them for their own week only, or undo them. */
function EveryWeekChanges({ changes }: { changes: ClassChange[] }) {
  const answer = useAnswerChange()
  return (
    <section aria-labelledby="every-week-title" className="space-y-2 rounded-2xl bg-card p-4 text-card-foreground md:p-5">
      <h2 id="every-week-title" className="text-base font-medium">
        Changed every week
      </h2>
      <ul className="divide-y divide-border">
        {changes.map((change) => {
          const name = `${change.course_code} Section ${change.section_code}`
          return (
            <li key={change.id} className="flex flex-wrap items-center justify-between gap-2 py-2">
              <p className="text-sm">
                <span className="font-medium">{name}</span> · from {formatDay(change.date)}
                <span className="block text-muted-foreground tabular-nums">{changeText(change)}</span>
              </p>
              <div className="flex flex-wrap gap-2">
                <Button
                  size="sm"
                  variant="outline"
                  disabled={answer.isPending}
                  aria-label={`Keep the change to ${name} for ${formatDay(change.date)} only`}
                  onClick={() => answer.mutate({ id: change.id, answer: 'confirm', everyWeek: false })}
                >
                  That week only
                </Button>
                <Button
                  size="sm"
                  variant="ghost"
                  disabled={answer.isPending}
                  aria-label={`Undo the change to ${name}`}
                  onClick={() => answer.mutate({ id: change.id, answer: 'reject' })}
                >
                  Undo
                </Button>
              </div>
            </li>
          )
        })}
      </ul>
      {answer.isError && (
        <p role="alert" className="text-sm text-destructive">
          {answer.error.message}
        </p>
      )}
    </section>
  )
}

function ChangeCard({ change }: { change: ClassChange }) {
  const answer = useAnswerChange()
  const name = `${change.course_code} Section ${change.section_code}`
  return (
    <li className="space-y-3 p-4">
      <div className="flex flex-wrap items-center gap-2">
        <p className="font-medium">
          {name} · {formatDay(change.date)}
        </p>
        {change.not_confirmed && <Badge variant="outline">Not confirmed</Badge>}
      </div>
      <p className="text-base font-medium tabular-nums">{changeText(change)}</p>
      {change.evidence.map((evidence) => (
        <blockquote key={evidence.sent_at + evidence.quote} className="border-l-2 border-border pl-3 text-sm text-muted-foreground">
          “{evidence.quote}”
          <span className="block text-xs">
            {evidence.sender_name || 'Someone'} in {evidence.group}
          </span>
        </blockquote>
      ))}
      {change.can_repeat && <p className="text-sm text-muted-foreground">Is this for this week only, or every week from now on?</p>}
      <div className="flex flex-wrap gap-2">
        {change.can_repeat ? (
          <>
            <Button
              size="sm"
              disabled={answer.isPending}
              aria-label={`Confirm change to ${name} for this week only`}
              onClick={() => answer.mutate({ id: change.id, answer: 'confirm', everyWeek: false })}
            >
              This week only
            </Button>
            <Button
              size="sm"
              variant="outline"
              disabled={answer.isPending}
              aria-label={`Confirm change to ${name} for every week`}
              onClick={() => answer.mutate({ id: change.id, answer: 'confirm', everyWeek: true })}
            >
              Every week
            </Button>
          </>
        ) : (
          <Button
            size="sm"
            disabled={answer.isPending}
            aria-label={`Confirm change to ${name}`}
            onClick={() => answer.mutate({ id: change.id, answer: 'confirm' })}
          >
            Confirm
          </Button>
        )}
        <Button
          size="sm"
          variant="outline"
          disabled={answer.isPending}
          aria-label={`Reject change to ${name}`}
          onClick={() => answer.mutate({ id: change.id, answer: 'reject' })}
        >
          Reject
        </Button>
      </div>
      {answer.isError && (
        <p role="alert" className="text-sm text-destructive">
          {answer.error.message}
        </p>
      )}
    </li>
  )
}
