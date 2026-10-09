/** Shapes of the "For you" feed API (/api/v1/feed/). */

export type Tier = 'direct' | 'action' | 'important' | 'digest'

/** One item of my feed: what UniFlow found (or staff posted), plus why I see it. */
export type FeedItem = {
  id: number // the insight's id
  kind: string
  info_type: string // e.g. "internship"; "" if none
  tier: Tier
  title: string
  summary: string
  importance: number
  relevance: number
  reason: string // e.g. "You are in CDE2313 Section A"
  action_required: boolean
  action_text: string
  starts_at: string | null
  deadline_at: string | null
  location: string
  link: string
  not_confirmed: boolean // the AI wasn't sure
  official: boolean // posted by staff
  read: boolean
  published_at: string
}

/** An original message the item came from. */
export type Evidence = {
  group: { id: number; platform: string; title: string }
  sender_name: string
  sent_at: string
  quote: string
  open_url: string // the Telegram post or the WhatsApp group; "" if none
}

/** GET feed/{id}/ */
export type FeedDetail = FeedItem & {
  data: Record<string, unknown>
  topics: string[]
  evidence: Evidence[]
  timetable_change: { id: number; my_status: 'pending' | 'confirmed' | 'rejected' } | null
  dismissed: boolean
}

/** GET feed/digest/ - one day's daily digest (date is null when there's none yet). */
export type Digest = {
  date: string | null
  items: FeedItem[]
}
