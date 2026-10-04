import { useState, type FormEvent } from 'react'

import { ApiError } from '@/api/errors'
import { EmptyState } from '@/components/EmptyState'
import { ErrorState } from '@/components/ErrorState'
import { PageLoading } from '@/components/PageLoading'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { useCreateSource, useMySources, usePasteMessages, useUploadExport } from '@/hooks/useSources'
import type { ImportResult, Source } from '@/types/sources'

/** The backend's own explanation (e.g. "Upload the .txt file…"), not just "Invalid input.". */
function errorText(error: Error): string {
  if (error instanceof ApiError) {
    const details = Object.values(error.fields).flat()
    if (details.length) return details.join(' ')
  }
  return error.message
}

function resultText({ added, already_stored }: ImportResult): string {
  const added_text = `${added} new message${added === 1 ? '' : 's'} added`
  return already_stored ? `${added_text} (${already_stored} UniFlow already had).` : `${added_text}.`
}

/** /sources — "Groups": my groups, add one, and feed it messages by hand. */
export function SourcesPage() {
  const sources = useMySources()

  return (
    <div className="max-w-3xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Groups</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Add the academic WhatsApp and Telegram groups you're in. For now, paste messages or
          upload a WhatsApp chat export; soon UniFlow will join your groups by itself.
        </p>
      </div>

      <AddGroupForm />

      {sources.isPending ? (
        <PageLoading />
      ) : sources.isError ? (
        <ErrorState title="Could not load your groups" />
      ) : sources.data.length === 0 ? (
        <EmptyState
          title="No groups yet"
          description="Add a group above, then paste its messages or upload its WhatsApp export."
        />
      ) : (
        <ul className="space-y-3">
          {sources.data.map((source) => (
            <GroupCard key={source.id} source={source} />
          ))}
        </ul>
      )}
    </div>
  )
}

function AddGroupForm() {
  const [title, setTitle] = useState('')
  const create = useCreateSource()

  function onSubmit(event: FormEvent) {
    event.preventDefault()
    if (title.trim()) create.mutate(title.trim(), { onSuccess: () => setTitle('') })
  }

  return (
    <form onSubmit={onSubmit} className="flex flex-wrap items-end gap-2">
      <div className="min-w-56 flex-1 space-y-1.5">
        <Label htmlFor="group-name">Group name</Label>
        <Input
          id="group-name"
          placeholder="e.g. CDE2313 Section A"
          value={title}
          onChange={(event) => setTitle(event.target.value)}
        />
      </div>
      <Button type="submit" disabled={create.isPending || !title.trim()}>
        Add group
      </Button>
      {create.isError && (
        <p role="alert" className="w-full text-sm text-destructive">
          {errorText(create.error)}
        </p>
      )}
    </form>
  )
}

function GroupCard({ source }: { source: Source }) {
  const [open, setOpen] = useState<'none' | 'paste' | 'upload'>('none')
  const toggle = (panel: 'paste' | 'upload') => setOpen(open === panel ? 'none' : panel)

  return (
    <li className="space-y-3 rounded-2xl bg-card p-4 shadow-sm ring-1 ring-border">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <p className="font-medium">{source.title}</p>
          <p className="text-sm text-muted-foreground">
            {source.platform_label} · {source.message_count} message
            {source.message_count === 1 ? '' : 's'}
          </p>
        </div>
        <div className="flex gap-2">
          <Button size="sm" variant={open === 'paste' ? 'default' : 'outline'} onClick={() => toggle('paste')}>
            Paste messages
          </Button>
          <Button size="sm" variant={open === 'upload' ? 'default' : 'outline'} onClick={() => toggle('upload')}>
            Upload WhatsApp export
          </Button>
        </div>
      </div>
      {open === 'paste' && <PasteForm source={source} />}
      {open === 'upload' && <UploadForm source={source} />}
    </li>
  )
}

function PasteForm({ source }: { source: Source }) {
  const [text, setText] = useState('')
  const paste = usePasteMessages()

  function onSubmit(event: FormEvent) {
    event.preventDefault()
    paste.mutate({ id: source.id, text }, { onSuccess: () => setText('') })
  }

  return (
    <form onSubmit={onSubmit} className="space-y-2">
      <Label htmlFor={`paste-${source.id}`}>Messages</Label>
      <textarea
        id={`paste-${source.id}`}
        rows={6}
        value={text}
        onChange={(event) => setText(event.target.value)}
        placeholder="Select messages in WhatsApp, copy them, and paste them here."
        className="w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-xs outline-none focus-visible:ring-2 focus-visible:ring-ring"
      />
      <Button type="submit" size="sm" disabled={paste.isPending || !text.trim()}>
        {paste.isPending ? 'Adding…' : 'Add messages'}
      </Button>
      <Outcome result={paste.data} error={paste.error} />
    </form>
  )
}

function UploadForm({ source }: { source: Source }) {
  const [file, setFile] = useState<File | null>(null)
  const upload = useUploadExport()

  function onSubmit(event: FormEvent) {
    event.preventDefault()
    if (file) upload.mutate({ id: source.id, file })
  }

  return (
    <form onSubmit={onSubmit} className="space-y-2">
      <Label htmlFor={`upload-${source.id}`}>WhatsApp export (.txt)</Label>
      <p className="text-xs text-muted-foreground">
        In WhatsApp: open the group → ⋮ → More → Export chat → Without media.
      </p>
      <Input
        id={`upload-${source.id}`}
        type="file"
        accept=".txt,text/plain"
        onChange={(event) => setFile(event.target.files?.[0] ?? null)}
      />
      <Button type="submit" size="sm" disabled={upload.isPending || !file}>
        {upload.isPending ? 'Uploading…' : 'Upload'}
      </Button>
      <Outcome result={upload.data} error={upload.error} />
    </form>
  )
}

function Outcome({ result, error }: { result?: ImportResult; error: Error | null }) {
  if (error) {
    return (
      <p role="alert" className="text-sm text-destructive">
        {errorText(error)}
      </p>
    )
  }
  if (!result) return null
  return (
    <p role="status" className="text-sm text-emerald-700">
      {resultText(result)}
    </p>
  )
}
