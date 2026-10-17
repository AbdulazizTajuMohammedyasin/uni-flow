import { useState, type FormEvent } from 'react'

import { ApiError } from '@/api/errors'
import { EmptyState } from '@/components/EmptyState'
import { ErrorState } from '@/components/ErrorState'
import { PageHeader } from '@/components/PageHeader'
import { PageLoading } from '@/components/PageLoading'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  useConnectSource,
  useCreateSource,
  useMySources,
  usePasteMessages,
  useUploadExport,
} from '@/hooks/useSources'
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
      <PageHeader
        title="Groups"
        description="Add the academic WhatsApp groups you're in with their invite link, and UniFlow's own number joins them. You can also paste messages or upload a WhatsApp chat export."
      />

      <AddGroupForm />

      {sources.isPending ? (
        <PageLoading />
      ) : sources.isError ? (
        <ErrorState title="Could not load your groups" />
      ) : sources.data.length === 0 ? (
        <EmptyState
          title="No groups yet"
          description="Add a group above with its invite link, or paste its messages by hand."
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

/** Name + optional WhatsApp invite link. With a link UniFlow's number joins the group;
 * without one it's a group for pasting messages by hand. */
function AddGroupForm() {
  const [title, setTitle] = useState('')
  const [inviteUrl, setInviteUrl] = useState('')
  const create = useCreateSource()
  const connect = useConnectSource()
  const busy = create.isPending || connect.isPending
  const error = connect.error ?? create.error
  const done = connect.data
  const clear = () => {
    setTitle('')
    setInviteUrl('')
  }

  function onSubmit(event: FormEvent) {
    event.preventDefault()
    if (!title.trim()) return
    if (inviteUrl.trim()) {
      create.reset()
      connect.mutate({ inviteUrl: inviteUrl.trim(), title: title.trim() }, { onSuccess: clear })
    } else {
      connect.reset()
      create.mutate(title.trim(), { onSuccess: clear })
    }
  }

  return (
    <form onSubmit={onSubmit} className="space-y-3 rounded-2xl bg-card p-4 shadow-sm ring-1 ring-border">
      <h2 className="font-semibold">Add a group</h2>
      <div className="grid gap-3 sm:grid-cols-2">
        <div className="space-y-1.5">
          <Label htmlFor="group-name">Group name</Label>
          <Input
            id="group-name"
            placeholder="What is it for? e.g. CDE2313 Section A"
            value={title}
            onChange={(event) => setTitle(event.target.value)}
          />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="group-link">WhatsApp invite link (optional)</Label>
          <Input
            id="group-link"
            placeholder="https://chat.whatsapp.com/…"
            value={inviteUrl}
            onChange={(event) => setInviteUrl(event.target.value)}
          />
        </div>
      </div>
      <p className="text-xs text-muted-foreground">
        In WhatsApp: open the group → tap its name → Invite via link → Copy link. Without a
        link, you can still paste the group's messages by hand.
      </p>
      <Button type="submit" disabled={busy || !title.trim()}>
        Add group
      </Button>
      {error && (
        <p role="alert" className="text-sm text-destructive">
          {errorText(error)}
        </p>
      )}
      {done && !error && (
        <p role="status" className="text-sm text-success">
          {done.status === 'pending'
            ? `Added "${done.title}". UniFlow's number will join it soon.`
            : `UniFlow already reads "${done.title}"; it's now in your groups.`}
        </p>
      )}
    </form>
  )
}

/** "Waiting to join" etc. next to the platform name. */
function statusText(source: Source): string {
  if (source.status === 'pending') return ' · Waiting for UniFlow to join'
  if (source.status === 'disconnected') return ' · Disconnected'
  return ''
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
            {statusText(source)}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
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
        className="w-full rounded-lg border border-input bg-card px-3 py-2 text-base shadow-xs outline-none focus-visible:ring-3 focus-visible:ring-ring/50 md:text-sm"
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
    <p role="status" className="text-sm text-success">
      {resultText(result)}
    </p>
  )
}
