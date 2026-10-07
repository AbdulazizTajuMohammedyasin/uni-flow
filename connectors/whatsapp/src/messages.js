// Turning a WhatsApp message (as Baileys gives it) into what the UniFlow backend expects.
// Plain functions with no WhatsApp connection, so they are easy to test.
import { normalizeMessageContent } from 'baileys'

/** Files UniFlow reads (the backend checks the real contents again). */
export const FILE_TYPES = new Set([
  'image/png',
  'image/jpeg',
  'image/webp',
  'application/pdf',
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
])

/** What UniFlow's number posts once when it joins a group (docs/08, principle 4). */
export const JOIN_NOTICE =
  'Hello! This is UniFlow, the student information assistant for AIU. A student added ' +
  'this group so UniFlow can pick out academic information (class changes, deadlines, ' +
  'opportunities) for the students who use it. UniFlow only reads this group: it never ' +
  'replies or messages anyone. A group admin can remove this number at any time to stop it.'

/** The code at the end of an invite link: https://chat.whatsapp.com/AbCd123 -> "AbCd123". */
export function inviteCode(link) {
  const match = /^https:\/\/chat\.whatsapp\.com\/(?:invite\/)?([A-Za-z0-9]+)\/?$/.exec(link.trim())
  return match ? match[1] : null
}

function seconds(timestamp) {
  // Baileys gives a number or a "Long" object (with toNumber()).
  return typeof timestamp === 'number' ? timestamp : Number(timestamp?.toNumber?.() ?? timestamp)
}

/** The sender as a WhatsApp id. Prefers the private "@lid" id over the phone-number one;
 * the backend scrambles it again either way, so a phone number is never stored. */
function senderRef(key) {
  const ids = [key.participant, key.participantAlt].filter(Boolean)
  return ids.find((id) => id.endsWith('@lid')) ?? ids[0] ?? ''
}

/** The file in a message that UniFlow reads, or null. */
export function attachedFile(content) {
  if (content?.imageMessage) {
    const image = content.imageMessage
    return { kind: 'imageMessage', mimeType: image.mimetype || 'image/jpeg', fileName: 'photo.jpg' }
  }
  const document = content?.documentMessage
  if (document && FILE_TYPES.has(document.mimetype)) {
    return { kind: 'documentMessage', mimeType: document.mimetype, fileName: document.fileName || 'file' }
  }
  return null
}

/**
 * A group message for POST internal/messages/, or null when UniFlow ignores it:
 * private chats, status updates, UniFlow's own messages, and messages with neither
 * text nor a readable file (stickers, reactions, joins…).
 */
export function toUniFlowMessage(message) {
  const key = message.key ?? {}
  if (!key.remoteJid?.endsWith('@g.us') || key.fromMe || !key.id) return null

  const content = normalizeMessageContent(message.message)
  const inner =
    content?.extendedTextMessage ?? content?.imageMessage ?? content?.documentMessage ?? null
  const text = content?.conversation || inner?.text || inner?.caption || ''
  const file = attachedFile(content)
  if (!text.trim() && !file) return null

  return {
    source_external_id: key.remoteJid,
    message_id: key.id,
    sender_ref: senderRef(key),
    sender_name: message.pushName ?? '',
    text,
    sent_at: new Date(seconds(message.messageTimestamp) * 1000).toISOString(),
    reply_to: inner?.contextInfo?.stanzaId ?? null,
    has_files: file !== null,
  }
}
