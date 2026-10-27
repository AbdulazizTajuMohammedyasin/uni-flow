import { Skeleton } from '@/components/ui/skeleton'
import { Switch } from '@/components/ui/switch'
import { usePushSettings, useUpdatePushSettings } from '@/hooks/useNotifications'
import type { PushSettings } from '@/types/notifications'

const SWITCHES: { key: keyof PushSettings; label: string; hint: string }[] = [
  { key: 'class_changes', label: 'Class changes', hint: 'A class of yours moved, was cancelled or changed room.' },
  { key: 'needs_you', label: 'When something needs you', hint: "You were named, there's something to do, or it's important." },
  { key: 'daily_digest', label: 'Daily digest', hint: 'The good-to-know items, once every evening.' },
]

/** Which alerts reach this phone (shown inside the UniFlow app only). Each switch saves at once. */
export function PushSettingsForm() {
  const settings = usePushSettings()
  const update = useUpdatePushSettings()

  if (settings.isPending) return <Skeleton className="h-36 w-full rounded-xl" />
  if (settings.isError) {
    return (
      <p role="alert" className="text-sm text-destructive">
        Couldn't load your phone notifications. {settings.error.message}
      </p>
    )
  }

  return (
    <div className="space-y-4">
      <ul className="divide-y divide-border">
        {SWITCHES.map(({ key, label, hint }) => (
          <li key={key} className="flex items-center justify-between gap-4 py-3 first:pt-0 last:pb-0">
            <label htmlFor={`push-${key}`} className="text-sm">
              <span className="font-medium">{label}</span>
              <span id={`push-${key}-hint`} className="block text-muted-foreground">
                {hint}
              </span>
            </label>
            <Switch
              id={`push-${key}`}
              aria-describedby={`push-${key}-hint`}
              checked={settings.data[key]}
              disabled={update.isPending}
              onCheckedChange={(checked) => update.mutate({ [key]: checked })}
            />
          </li>
        ))}
      </ul>
      {update.isError && (
        <p role="alert" className="text-sm text-destructive">
          {update.error.message}
        </p>
      )}
    </div>
  )
}
