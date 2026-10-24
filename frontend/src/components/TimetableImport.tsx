import { useState, type FormEvent } from 'react'

import { ApiError } from '@/api/errors'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  useChooseImportTab,
  useConfirmImport,
  useDiscardImport,
  useStartImport,
  useTimetableImport,
  useTimetableImports,
} from '@/hooks/useTimetable'
import type { SemesterChoice, ImportRow, TimetableImport } from '@/types/timetable'

import { SelectField } from './SelectField'

const ACCEPTED = '.png,.jpg,.jpeg,.webp,.pdf,.xlsx'

/** The backend's own explanation (e.g. "Download it as Excel…"), not just "Invalid input.". */
function errorText(error: Error): string {
  if (error instanceof ApiError) {
    const details = Object.values(error.fields).flat()
    if (details.length) return details.join(' ')
  }
  return error.message
}

function meetingsText(row: ImportRow): string {
  return row.meetings
    .map((m) => {
      const day = m.day.charAt(0).toUpperCase() + m.day.slice(1, 3)
      return `${day} ${m.start}–${m.end}${m.room ? ` · ${m.room}` : ''}`
    })
    .join(', ')
}

/** "Add my timetable": upload a file or give a link → the AI reads it → check → confirm. */
export function TimetableImportBox({ semester = 'current' }: { semester?: SemesterChoice }) {
  const [importId, setImportId] = useState<number | null>(null)
  const current = useTimetableImport(importId)
  const reset = () => setImportId(null)

  if (importId === null) return <StartForm semester={semester} onStarted={setImportId} />
  if (current.isPending) return <p role="status">Loading…</p>
  if (current.isError) return <p role="alert">{errorText(current.error)}</p>

  const timetableImport = current.data
  switch (timetableImport.status) {
    case 'reading':
      return (
        <p role="status" className="text-sm">
          Reading your timetable… this can take up to a minute.
        </p>
      )
    case 'failed':
      return (
        <div className="space-y-2">
          <p role="alert" className="text-sm text-destructive">
            {timetableImport.error}
          </p>
          <Button size="sm" variant="outline" onClick={reset}>
            Try another file
          </Button>
        </div>
      )
    case 'ready':
      return <Review timetableImport={timetableImport} onDone={reset} />
    case 'confirmed':
      return <Confirmed timetableImport={timetableImport} onDone={reset} />
    default:
      return <StartForm semester={semester} onStarted={setImportId} />
  }
}

/** A timetable someone shared in one of my groups, already read for me (M6.5). */
export function GroupTimetableOffer() {
  const imports = useTimetableImports()
  const offer = imports.data?.find((item) => item.status === 'ready' && item.group)
  if (!offer) return null
  return (
    <section
      aria-label="Timetable shared in a group"
      className="space-y-3 rounded-2xl bg-card p-6 shadow-sm ring-1 ring-primary/40"
    >
      <p className="text-sm text-muted-foreground">
        A timetable was shared in <span className="font-medium text-foreground">{offer.group}</span>.
      </p>
      <Review timetableImport={offer} onDone={() => imports.refetch()} />
    </section>
  )
}

function StartForm({ semester, onStarted }: { semester: SemesterChoice; onStarted: (id: number) => void }) {
  const [file, setFile] = useState<File | null>(null)
  const [link, setLink] = useState('')
  const start = useStartImport()

  function submit(event: FormEvent, input: { file: File } | { link: string }) {
    event.preventDefault()
    start.mutate({ input, semester }, { onSuccess: (created) => onStarted(created.id) })
  }

  return (
    <div className="space-y-4">
      <p className="text-sm text-muted-foreground">
        Upload your timetable (a photo, PDF or Excel file) or paste a Google Drive link. UniFlow
        reads it and shows you the classes before anything is saved.
      </p>
      <form onSubmit={(event) => file && submit(event, { file })} className="flex flex-wrap items-end gap-2">
        <div className="min-w-56 flex-1 space-y-1.5">
          <Label htmlFor="timetable-file">Timetable file</Label>
          <Input
            id="timetable-file"
            type="file"
            accept={ACCEPTED}
            onChange={(event) => setFile(event.target.files?.[0] ?? null)}
          />
        </div>
        <Button type="submit" disabled={!file || start.isPending}>
          Read timetable
        </Button>
      </form>
      <form onSubmit={(event) => link.trim() && submit(event, { link: link.trim() })} className="flex flex-wrap items-end gap-2">
        <div className="min-w-56 flex-1 space-y-1.5">
          <Label htmlFor="timetable-link">…or a Google Drive / Sheets link</Label>
          <Input
            id="timetable-link"
            placeholder="https://docs.google.com/spreadsheets/d/…"
            value={link}
            onChange={(event) => setLink(event.target.value)}
          />
        </div>
        <Button type="submit" variant="outline" disabled={!link.trim() || start.isPending}>
          Read link
        </Button>
      </form>
      <p className="text-xs text-muted-foreground">
        Link only opens with your AIU account? Open it, choose File → Download → Microsoft Excel
        (.xlsx), then upload that file above.
      </p>
      {start.isError && (
        <p role="alert" className="text-sm text-destructive">
          {errorText(start.error)}
        </p>
      )}
    </div>
  )
}

function Review({ timetableImport, onDone }: { timetableImport: TimetableImport; onDone: () => void }) {
  const [skipped, setSkipped] = useState<string[]>([])
  const chooseTab = useChooseImportTab()
  const confirm = useConfirmImport()
  const discard = useDiscardImport()
  const key = (row: ImportRow) => `${row.course_code}-${row.section}`
  const kept = timetableImport.rows.filter((row) => !skipped.includes(key(row)))

  return (
    <div className="space-y-4">
      <h3 className="font-medium">Is this your timetable?</h3>
      {timetableImport.tabs.length > 1 && (
        <SelectField
          label="Tab"
          value={timetableImport.tab}
          onChange={(event) => {
            setSkipped([])
            chooseTab.mutate({ id: timetableImport.id, tab: event.target.value })
          }}
        >
          {timetableImport.tabs.map((tab) => (
            <option key={tab} value={tab}>
              {tab}
            </option>
          ))}
        </SelectField>
      )}
      <p className="text-sm text-muted-foreground">Untick any class you don't take.</p>
      <ul className="divide-y divide-border rounded-xl ring-1 ring-border">
        {timetableImport.rows.map((row) => (
          <li key={key(row)} className="p-3">
            <label className="flex items-start gap-3">
              <input
                type="checkbox"
                className="mt-1"
                checked={!skipped.includes(key(row))}
                onChange={(event) =>
                  setSkipped((list) =>
                    event.target.checked ? list.filter((k) => k !== key(row)) : [...list, key(row)],
                  )
                }
              />
              <span className="min-w-0">
                <span className="block font-medium">
                  {row.course_code} · Section {row.section}
                </span>
                <span className="block truncate text-sm text-muted-foreground">
                  {row.course_name}
                  {row.lecturer && ` · ${row.lecturer}`}
                </span>
                <span className="block text-xs text-muted-foreground">{meetingsText(row)}</span>
              </span>
            </label>
          </li>
        ))}
      </ul>
      <div className="flex flex-wrap gap-2">
        <Button
          disabled={kept.length === 0 || confirm.isPending}
          onClick={() => confirm.mutate({ id: timetableImport.id, rows: kept })}
        >
          Confirm {kept.length} class{kept.length === 1 ? '' : 'es'}
        </Button>
        <Button
          variant="ghost"
          disabled={discard.isPending}
          onClick={() => discard.mutate(timetableImport.id, { onSuccess: onDone })}
        >
          Not my timetable
        </Button>
      </div>
      {(confirm.error ?? chooseTab.error) && (
        <p role="alert" className="text-sm text-destructive">
          {errorText((confirm.error ?? chooseTab.error) as Error)}
        </p>
      )}
    </div>
  )
}

function Confirmed({ timetableImport, onDone }: { timetableImport: TimetableImport; onDone: () => void }) {
  const added = timetableImport.report.enrolled?.length ?? 0
  const differences = timetableImport.report.differences?.length ?? 0
  return (
    <div className="space-y-2">
      <p role="status" className="text-sm text-success">
        Added {added} class{added === 1 ? '' : 'es'} to your timetable.
        {differences > 0 &&
          ` ${differences} already existed with different times; UniFlow kept the existing times.`}
      </p>
      <Button size="sm" variant="outline" onClick={onDone}>
        Done
      </Button>
    </div>
  )
}
