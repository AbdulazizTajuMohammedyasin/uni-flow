/** Shapes of the sources API (/api/v1/sources/). A "source" is a group or channel. */

export type Source = {
  id: number
  title: string
  platform: 'whatsapp_group' | 'telegram_group' | 'telegram_channel' | 'staff' | 'manual'
  platform_label: string
  status: 'pending' | 'active' | 'disconnected'
  school: number | null
  programme: number | null
  intake: number | null
  course: number | null
  section: number | null
  message_count: number
  /** I add UniFlow's number to this group myself (no invite link). */
  added_by_number: boolean
  /** UniFlow's WhatsApp number, while such a group waits for it (blank otherwise). */
  uniflow_number: string
}

/** A group UniFlow joined without an invite link that nobody has claimed: maybe mine, if I typed
 * a different name (GET sources/{id}/unclaimed/). */
export type UnclaimedGroup = {
  id: number
  title: string
  joined_at: string
}

/** The answer to pasting or uploading messages. */
export type ImportResult = {
  added: number
  already_stored: number
}
