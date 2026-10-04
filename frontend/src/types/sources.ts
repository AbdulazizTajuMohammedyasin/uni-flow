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
}

/** The answer to pasting or uploading messages. */
export type ImportResult = {
  added: number
  already_stored: number
}
