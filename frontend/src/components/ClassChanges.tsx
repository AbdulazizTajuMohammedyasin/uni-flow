import { CircleAlert } from 'lucide-react'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { useAnswerChange, useClassChanges } from '@/hooks/useTimetable'
import { changeText, formatDay } from '@/lib/timetable'
import type { ClassChange } from '@/types/timetable'

/** Changes the AI found in group messages that I haven't answered yet. My timetable
 * changes only if I confirm (and only mine, not my classmates'). */
export function ClassChanges() {
  const changes = useClassChanges()
  const waiting = changes.data?.filter((change) => change.my_status === 'pending') ?? []
  if (waiting.length === 0) return null

  return (
    <section aria-label="Changes to confirm" className="space-y-3 rounded-xl bg-attention p-4 ring-1 ring-attention-border md:p-5">
      <div>
        <h2 className="flex items-center gap-2 font-semibold">
          <CircleAlert aria-hidden className="size-[1.125rem] text-attention-foreground" />
          {waiting.length === 1 ? 'A class may have changed' : `${waiting.length} classes may have changed`}
        </h2>
        <p className="mt-0.5 text-sm text-foreground">
          UniFlow found this in a group message. Only your own timetable changes, and only if you confirm.
        </p>
      </div>
      <ul className="divide-y divide-border overflow-hidden rounded-lg bg-card ring-1 ring-border">
        {waiting.map((change) => (
          <ChangeCard key={change.id} change={change} />
        ))}
      </ul>
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
      <p className="text-base font-semibold tabular-nums">{changeText(change)}</p>
      {change.evidence.map((evidence) => (
        <blockquote key={evidence.sent_at + evidence.quote} className="border-l-2 border-border pl-3 text-sm text-muted-foreground">
          “{evidence.quote}”
          <span className="block text-xs">
            {evidence.sender_name || 'Someone'} in {evidence.group}
          </span>
        </blockquote>
      ))}
      <div className="flex flex-wrap gap-2">
        <Button
          size="sm"
          disabled={answer.isPending}
          aria-label={`Confirm change to ${name}`}
          onClick={() => answer.mutate({ id: change.id, answer: 'confirm' })}
        >
          Confirm
        </Button>
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
