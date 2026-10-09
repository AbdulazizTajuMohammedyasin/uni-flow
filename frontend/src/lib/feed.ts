import type { Tier } from '@/types/feed'

/** The four levels of the "For you" page, in order. */
export const TIERS: { tier: Tier; title: string; hint: string }[] = [
  { tier: 'direct', title: 'Direct attention', hint: 'You were named in these.' },
  { tier: 'action', title: 'Action required', hint: 'You need to do something.' },
  { tier: 'important', title: 'Important updates', hint: 'Changes that affect you.' },
  { tier: 'digest', title: 'Digest', hint: 'Good to know.' },
]

/** "2026-10-20T16:00:00Z" -> "Tue 21 Oct, 00:00" in Malaysia time (UniFlow's time zone). */
export function formatWhen(iso: string, withTime = true): string {
  return new Date(iso).toLocaleString('en-GB', {
    weekday: 'short',
    day: 'numeric',
    month: 'short',
    ...(withTime ? { hour: '2-digit', minute: '2-digit', hour12: false } : {}),
    timeZone: 'Asia/Kuala_Lumpur',
  })
}

/** "class_moved" -> "Class moved" */
export function kindLabel(kind: string): string {
  const text = kind.replace(/_/g, ' ')
  return text.charAt(0).toUpperCase() + text.slice(1)
}
