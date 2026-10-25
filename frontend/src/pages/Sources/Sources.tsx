import { useRef, useState, type FormEvent } from 'react'
import { Link } from 'react-router'
import {
  Building2,
  ChevronDown,
  CircleCheck,
  ClipboardPaste,
  Clock,
  FileUp,
  MessageCircle,
  Send,
  Trash2,
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
  useClaimGroup,
  useConnectSource,
  useCreateSource,
  useLeaveSource,
  useMySources,
  usePasteMessages,
  useUnclaimedGroups,
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
        description="Add the academic WhatsApp groups you're in. With an invite link UniFlow's own number joins by itself; without one, you add UniFlow's number to the group. You can also paste messages or upload a WhatsApp chat export."
      />

      <AddGroupForm />

      {sources.isPending ? (
        <PageLoading />
      ) : sources.isError ? (
        <ErrorState title="Could not load your groups" />
      ) : sources.data.length === 0 ? (
        <EmptyState
          title="No groups yet"
          description="Add a group above: with its invite link, by adding UniFlow's number to it, or by pasting its messages."
        />
      ) : (
        <ul className="divide-y divide-border overflow-hidden rounded-2xl bg-card dark:ring-1 dark:ring-border">
          {sources.data.map((source) => (
            <GroupCard key={source.id} source={source} />
          ))}
        </ul>
      )}
    </div>
  )
}

type Way = 'link' | 'number' | 'paste'

/** How UniFlow gets a group's messages. */
const WAYS: { value: Way; label: string; hint: string }[] = [
  {
    value: 'link',
    label: 'Invite link',
    hint: "In WhatsApp: open the group → tap its name → Invite via link → Copy link. UniFlow's number then joins by itself.",
  },
  {
    value: 'number',
    label: "I'll add UniFlow's number",
    hint: "For a group without an invite link. Add it here first, then add UniFlow's number to the group in WhatsApp (the steps appear below).",
  },
  {
    value: 'paste',
    label: "I'll paste messages",
    hint: 'Paste messages copied from WhatsApp, or upload a chat export, whenever you like.',
  },
]

/** A group's name and how UniFlow gets its messages: UniFlow's number joins by invite link,
 * the student adds UniFlow's number to the group, or the student pastes messages by hand. */
function AddGroupForm() {
  const [title, setTitle] = useState('')
  const [way, setWay] = useState<Way>('link')
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

  const missing = !title.trim() ? 'Type a group name first.' : way === 'link' && !inviteUrl.trim() ? 'Paste the invite link, or choose another way.' : ''

  function onSubmit(event: FormEvent) {
    event.preventDefault()
    if (missing) return
    if (way === 'paste') {
      connect.reset()
      create.mutate(title.trim(), { onSuccess: clear })
    } else {
      create.reset()
      connect.mutate({ inviteUrl: way === 'link' ? inviteUrl.trim() : '', title: title.trim() }, { onSuccess: clear })
    }
  }

  return (
    <form onSubmit={onSubmit} className="space-y-3 rounded-2xl bg-card p-4 md:p-6 dark:ring-1 dark:ring-border">
      <h2 className="font-medium">Add a group</h2>
      <div className="grid gap-3 sm:grid-cols-2">
        <div className="space-y-1.5">
          <Label htmlFor="group-name">Group name</Label>
          <Input
            id="group-name"
            placeholder={way === 'number' ? 'Exactly as in WhatsApp' : 'What is it for? e.g. CDE2313 Section A'}
            value={title}
            onChange={(event) => setTitle(event.target.value)}
            aria-describedby={way === 'number' ? 'group-name-hint' : undefined}
          />
          {way === 'number' && (
            <p id="group-name-hint" className="text-xs text-muted-foreground">
              Type the group's name exactly as it shows in WhatsApp: UniFlow recognises the group by it.
            </p>
          )}
        </div>
        {way === 'link' && (
          <div className="space-y-1.5">
            <Label htmlFor="group-link">WhatsApp invite link</Label>
            <Input
              id="group-link"
              placeholder="https://chat.whatsapp.com/…"
              value={inviteUrl}
              onChange={(event) => setInviteUrl(event.target.value)}
            />
          </div>
        )}
      </div>
      <fieldset>
        <legend className="text-sm font-medium">How UniFlow gets its messages</legend>
        <div className="mt-2 flex flex-wrap gap-2">
          {WAYS.map((option) => (
            <label key={option.value} className="cursor-pointer">
              <input
                type="radio"
                name="group-way"
                value={option.value}
                checked={way === option.value}
                onChange={() => setWay(option.value)}
                className="peer sr-only"
              />
              <span className="inline-flex min-h-11 items-center rounded-full border border-border px-3.5 text-sm peer-checked:border-primary peer-checked:bg-primary peer-checked:font-medium peer-checked:text-primary-foreground peer-focus-visible:ring-3 peer-focus-visible:ring-ring/50 md:min-h-9">
                {option.label}
              </span>
            </label>
          ))}
        </div>
        <p className="mt-2 text-xs text-muted-foreground">{WAYS.find((option) => option.value === way)!.hint}</p>
      </fieldset>
      <div className="flex flex-wrap items-center gap-3">
        <Button type="submit" disabled={busy || Boolean(missing)} aria-describedby={missing ? 'add-group-hint' : undefined}>
          Add group
        </Button>
        {missing && (
          <p id="add-group-hint" className="text-sm text-muted-foreground">
            {missing}
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
          {done.added_by_number
            ? `Added "${done.title}". Now add UniFlow's number to the group in WhatsApp: see the steps below.`
            : done.status === 'pending'
              ? `Added "${done.title}". UniFlow's number will join it soon.`
              : `UniFlow already reads "${done.title}"; it's now in your groups.`}
        </p>
      )}
    </form>
  )
}

const PANEL_TITLES: Record<Exclude<Panel, 'none'>, string> = {
  paste: 'Paste messages',
  upload: 'Upload a WhatsApp export',
  remove: 'Remove from my groups?',
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
      <Badge variant="outline">
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
    <Badge>
      <CircleCheck aria-hidden />
      Connected
    </Badge>
  )
}

type Panel = 'none' | 'paste' | 'upload' | 'remove'

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
            {source.status === 'pending' &&
              (source.added_by_number ? (
                <AddNumberSteps source={source} />
              ) : (
                <p className="text-sm text-muted-foreground">UniFlow's number will join soon; then new messages arrive by themselves.</p>
              ))}
            {source.status === 'disconnected' && (
              <p className="text-sm text-muted-foreground">New messages from this group are ignored.</p>
            )}
          </div>
        </div>
        <div className="flex items-center gap-1">
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
          <Button
            size="icon-sm"
            variant="ghost"
            aria-label={`Remove ${source.title} from my groups`}
            aria-expanded={open === 'remove'}
            onClick={() => setOpen(open === 'remove' ? 'none' : 'remove')}
          >
            <Trash2 aria-hidden />
          </Button>
        </div>
      </div>
      {open !== 'none' && (
        <div className="space-y-2 rounded-xl bg-muted/60 p-3">
          <div className="flex items-center justify-between gap-2">
            <h3 className="text-sm font-medium">{PANEL_TITLES[open]}</h3>
            <Button size="icon-sm" variant="ghost" aria-label="Close" onClick={() => setOpen('none')}>
              <X aria-hidden />
            </Button>
          </div>
          {open === 'paste' && <PasteForm source={source} />}
          {open === 'upload' && <UploadForm source={source} />}
          {open === 'remove' && <LeaveConfirm source={source} onCancel={() => setOpen('none')} />}
        </div>
      )}
    </li>
  )
}

/** For a group added without an invite link: how to put UniFlow's number in it. UniFlow
 * recognises it by name; if the name differs, I pick it from the groups UniFlow joined. */
function AddNumberSteps({ source }: { source: Source }) {
  return (
    <div className="mt-2 max-w-[65ch] space-y-3">
      <ol className="list-decimal space-y-2 pl-5 text-sm text-muted-foreground">
        <li>
          {source.uniflow_number ? (
            <span className="inline-flex flex-wrap items-center gap-x-2 gap-y-1">
              Save UniFlow's number as a contact:
              <span className="font-medium text-foreground tabular-nums">{source.uniflow_number}</span>
              <CopyButton text={source.uniflow_number} label="Copy number" />
            </span>
          ) : (
            "Ask the UniFlow team for UniFlow's WhatsApp number, and save it as a contact."
          )}
        </li>
        <li>In the WhatsApp group: tap its name → Add member → choose UniFlow. If only admins can add members, ask an admin.</li>
        <li>
          Let the group know UniFlow reads it (
          <Link to="/privacy" className="text-foreground underline underline-offset-4 hover:decoration-2">
            what UniFlow reads
          </Link>
          ).
        </li>
      </ol>
      <p className="text-sm text-muted-foreground">
        UniFlow recognises the group by its name, "{source.title}", and connects within a minute of being added.
      </p>
      <UnclaimedGroups source={source} />
    </div>
  )
}

/** If the WhatsApp name differs from what I typed: the groups UniFlow joined since, to pick mine. */
function UnclaimedGroups({ source }: { source: Source }) {
  const groups = useUnclaimedGroups(source.id)
  const claim = useClaimGroup()
  if (!groups.data?.length) return null
  return (
    <div className="space-y-2 rounded-xl bg-muted/60 p-3">
      <p className="text-sm text-foreground">
        {groups.data.length === 1
          ? "UniFlow joined this group since you added yours. If it's yours (its WhatsApp name is different), choose it:"
          : 'UniFlow joined these groups since you added yours. If one is yours (its WhatsApp name is different), choose it:'}
      </p>
      <ul className="space-y-2">
        {groups.data.map((group) => (
          <li key={group.id} className="flex flex-wrap items-center justify-between gap-2">
            <span className="text-sm font-medium">{group.title}</span>
            <Button
              size="sm"
              variant="outline"
              disabled={claim.isPending}
              aria-label={`This is my group: ${group.title}`}
              onClick={() => claim.mutate({ id: source.id, groupId: group.id })}
            >
              This is my group
            </Button>
          </li>
        ))}
      </ul>
      {claim.error && (
        <p role="alert" className="text-sm text-destructive">
          {errorText(claim.error)}
        </p>
      )}
    </div>
  )
}

/** Copies a number or code; says "Copied" for a moment (announced to screen readers). */
function CopyButton({ text, label }: { text: string; label: string }) {
  const [copied, setCopied] = useState(false)
  async function copy() {
    await navigator.clipboard?.writeText(text)
    setCopied(true)
    window.setTimeout(() => setCopied(false), 2000)
  }
  return (
    <Button type="button" size="sm" variant="outline" onClick={copy}>
      <span aria-live="polite">{copied ? 'Copied' : label}</span>
    </Button>
  )
}

/** Taking a group off my list, once I confirm. The group itself stays for the others who added it. */
function LeaveConfirm({ source, onCancel }: { source: Source; onCancel: () => void }) {
  const leave = useLeaveSource()

  return (
    <div className="space-y-2">
      <p className="text-sm text-muted-foreground">
        You'll stop getting announcements just because you're in this group. Other students who added it keep it, and
        announcements for your courses still reach you. You can add it back anytime.
      </p>
      <div className="flex flex-wrap gap-2">
        <Button size="sm" variant="destructive" disabled={leave.isPending} onClick={() => leave.mutate(source.id)}>
          {leave.isPending ? 'Removing…' : 'Remove'}
        </Button>
        <Button size="sm" variant="outline" onClick={onCancel}>
          Cancel
        </Button>
      </div>
      {leave.error && (
        <p role="alert" className="text-sm text-destructive">
          {errorText(leave.error)}
        </p>
      )}
    </div>
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
        className="w-full rounded-md border border-input bg-card px-3 py-2 text-base outline-none focus-visible:ring-3 focus-visible:ring-ring/50 md:text-sm"
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
