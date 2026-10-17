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
    <section aria-label="Changes to confirm" className="space-y-3 rounded-2xl bg-attention p-4 ring-1 ring-attention-border">
      <h2 className="font-semibold">
        {waiting.length === 1 ? 'A class may have changed' : `${waiting.length} classes may have changed`}
      </h2>
      <ul className="space-y-3">
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
    <li className="space-y-2 rounded-xl bg-card p-3 shadow-sm ring-1 ring-border">
      <div className="flex flex-wrap items-center gap-2">
        <p className="font-medium">
          {name} · {formatDay(change.date)}
        </p>
        {change.not_confirmed && <Badge variant="outline">Not confirmed</Badge>}
      </div>
      <p className="text-sm">{changeText(change)}</p>
      {change.evidence.map((evidence) => (
        <blockquote key={evidence.sent_at + evidence.quote} className="border-l-2 border-border pl-3 text-sm text-muted-foreground">
          “{evidence.quote}”
          <span className="block text-xs">
            {evidence.sender_name || 'Someone'} in {evidence.group}
          </span>
        </blockquote>
      ))}
      <div className="flex gap-2">
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
