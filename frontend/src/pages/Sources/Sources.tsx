import { useRef, useState, type FormEvent } from 'react'
import {
  Building2,
  ChevronDown,
  CircleCheck,
  ClipboardPaste,
  Clock,
  FileUp,
  MessageCircle,
  Send,
  Unplug,
  X,
  type LucideIcon,
} from 'lucide-react'

import { ApiError } from '@/api/errors'
import { EmptyState } from '@/components/EmptyState'
import { ErrorState } from '@/components/ErrorState'
import { PageHeader } from '@/components/PageHeader'
import { PageLoading } from '@/components/PageLoading'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
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
        <ul className="divide-y divide-border overflow-hidden rounded-xl bg-card ring-1 ring-border">
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
      <div className="flex flex-wrap items-center gap-3">
        <Button type="submit" disabled={busy || !title.trim()} aria-describedby={title.trim() ? undefined : 'add-group-hint'}>
          Add group
        </Button>
        {!title.trim() && (
          <p id="add-group-hint" className="text-sm text-muted-foreground">
            Type a group name first.
          </p>
        )}
      </div>
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

const PLATFORM_ICONS: Record<Source['platform'], LucideIcon> = {
  whatsapp_group: MessageCircle,
  telegram_group: Send,
  telegram_channel: Send,
  staff: Building2,
  manual: ClipboardPaste,
}

/** Whether UniFlow's number or bot is in the group, as an icon plus a word (not colour alone).
 * Groups fed by hand or by staff have no connection, so no badge. */
function StatusBadge({ source }: { source: Source }) {
  if (source.platform === 'manual' || source.platform === 'staff') return null
  if (source.status === 'pending') {
    return (
      <Badge className="bg-attention text-attention-foreground">
        <Clock aria-hidden />
        Waiting to join
      </Badge>
    )
  }
  if (source.status === 'disconnected') {
    return (
      <Badge variant="destructive">
        <Unplug aria-hidden />
        Disconnected
      </Badge>
    )
  }
  return (
    <Badge className="bg-success/10 text-success">
      <CircleCheck aria-hidden />
      Connected
    </Badge>
  )
}

type Panel = 'none' | 'paste' | 'upload'

function GroupCard({ source }: { source: Source }) {
  const [open, setOpen] = useState<Panel>('none')
  // Choosing from the menu moves focus into the new form, not back to the menu button.
  const chosen = useRef<Panel>('none')
  const Icon = PLATFORM_ICONS[source.platform]
  const choose = (panel: Panel) => {
    chosen.current = panel
    setOpen(panel)
  }

  return (
    <li className="space-y-3 p-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="flex min-w-0 gap-3">
          <span className="mt-0.5 flex size-9 shrink-0 items-center justify-center rounded-full bg-muted text-muted-foreground">
            <Icon aria-hidden className="size-4" />
          </span>
          <div className="min-w-0 space-y-1">
            <div className="flex flex-wrap items-center gap-x-2 gap-y-1">
              <p className="font-medium">{source.title}</p>
              <StatusBadge source={source} />
            </div>
            <p className="text-sm text-muted-foreground">
              {source.platform_label} · {source.message_count} message
              {source.message_count === 1 ? '' : 's'}
            </p>
            {source.status === 'pending' && (
              <p className="text-sm text-muted-foreground">UniFlow's number will join soon; then new messages arrive by themselves.</p>
            )}
            {source.status === 'disconnected' && (
              <p className="text-sm text-muted-foreground">New messages from this group are ignored.</p>
            )}
          </div>
        </div>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button size="sm" variant="outline" aria-label={`Add messages to ${source.title}`}>
              Add messages
              <ChevronDown aria-hidden />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent
            align="end"
            className="w-auto min-w-56"
            onCloseAutoFocus={(event) => {
              if (chosen.current === 'none') return
              event.preventDefault()
              document.getElementById(`${chosen.current}-${source.id}`)?.focus()
              chosen.current = 'none'
            }}
          >
            <DropdownMenuItem onSelect={() => choose('paste')}>
              <ClipboardPaste aria-hidden />
              Paste messages
            </DropdownMenuItem>
            <DropdownMenuItem onSelect={() => choose('upload')}>
              <FileUp aria-hidden />
              Upload WhatsApp export
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
      {open !== 'none' && (
        <div className="space-y-2 rounded-lg bg-muted/50 p-3 ring-1 ring-border">
          <div className="flex items-center justify-between gap-2">
            <h3 className="text-sm font-semibold">{open === 'paste' ? 'Paste messages' : 'Upload a WhatsApp export'}</h3>
            <Button size="icon-sm" variant="ghost" aria-label="Close" onClick={() => setOpen('none')}>
              <X aria-hidden />
            </Button>
          </div>
          {open === 'paste' ? <PasteForm source={source} /> : <UploadForm source={source} />}
        </div>
      )}
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
      {/* The panel's "Paste messages" title already says what goes here. */}
      <Label htmlFor={`paste-${source.id}`} className="sr-only">
        Messages
      </Label>
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
