// The UniFlow WhatsApp connector: runs UniFlow's own WhatsApp number (docs/08).
//
// 1. Logs in (the first time: a pairing code you type in WhatsApp on the phone).
// 2. Every few minutes asks the backend which groups students added, and joins them
//    slowly (one at a time), silently (SEND_JOIN_NOTICE=true: posting the join notice once).
// 3. Forwards every new group message, then its photo/PDF/Excel file, to the backend.
// It ignores private chats and never sends anything except the join notice, if turned on.
// After a restart WhatsApp delivers what was missed; the backend stores each message once.
import makeWASocket, {
  DisconnectReason,
  downloadMediaMessage,
  fetchLatestWaWebVersion,
  normalizeMessageContent,
  useMultiFileAuthState,
} from 'baileys'

import { attachedFile, inviteCode, JOIN_NOTICE, toUniFlowMessage } from './messages.js'
import { createClient, UniFlowError } from './uniflow.js'

const config = {
  apiUrl: process.env.UNIFLOW_API_URL ?? 'http://127.0.0.1:8000/api/v1',
  secret: process.env.CONNECTOR_SECRET ?? '',
  number: (process.env.WHATSAPP_NUMBER ?? '').replace(/\D/g, ''), // digits only
  authDir: process.env.AUTH_DIR ?? './auth',
  joinEverySeconds: Number(process.env.JOIN_EVERY_SECONDS ?? 300),
  maxFileBytes: Number(process.env.MAX_UPLOAD_MB ?? 10) * 1024 * 1024,
  sendJoinNotice: process.env.SEND_JOIN_NOTICE === 'true', // off unless turned on
}
if (!config.secret) {
  console.error('Set CONNECTOR_SECRET in connectors/whatsapp/.env (the same as in backend/.env).')
  process.exit(1)
}

const uniflow = createClient(config)
const log = (...parts) => console.log(new Date().toISOString(), ...parts)

// Baileys writes a lot of internal detail; only warnings and errors are shown.
const quietLogger = {
  level: 'warn',
  child: () => quietLogger,
  trace() {},
  debug() {},
  info() {},
  warn: (...parts) => console.warn('[whatsapp]', ...parts),
  error: (...parts) => console.error('[whatsapp]', ...parts),
}

const lastTried = new Map() // pending group id -> when a join was last tried
const waitingApproval = new Map() // WhatsApp group id -> pending group id (admin must approve)
const announced = new Set() // groups whose join was reported since the connector started
let joinTimer = null

async function start() {
  const { state, saveCreds } = await useMultiFileAuthState(config.authDir)
  // WhatsApp refuses to link a device that reports an old WhatsApp Web version, and the
  // one built into Baileys 7.0.0-rc14 is already out of date: ask for the current one.
  const { version } = await fetchLatestWaWebVersion().catch(() => ({ version: undefined }))
  const socket = makeWASocket({
    auth: state,
    version,
    // Baileys' default device (Chrome on macOS). A custom name only works with QR-code
    // login; with a pairing code WhatsApp refuses it ("couldn't link device").
    logger: quietLogger,
    markOnlineOnConnect: false, // stay "offline", so members don't see UniFlow online
    syncFullHistory: false,
  })
  socket.ev.on('creds.update', saveCreds)
  let pairingRequested = false

  socket.ev.on('connection.update', async ({ connection, lastDisconnect, qr }) => {
    // Ask for a pairing code once: each new code cancels the previous one.
    if (qr && !socket.authState.creds.registered && !pairingRequested) {
      pairingRequested = true
      if (!config.number) {
        console.error('Set WHATSAPP_NUMBER in .env (with the country code) to log in.')
        process.exit(1)
      }
      const code = await socket.requestPairingCode(config.number)
      log(`Pairing code: ${code.slice(0, 4)}-${code.slice(4)}  (type the 8 characters within a minute)`)
      log('On the phone: WhatsApp > Linked devices > Link a device > Link with phone number instead')
    }
    if (connection === 'open') {
      log('Connected to WhatsApp.')
      clearInterval(joinTimer)
      joinTimer = setInterval(() => joinPendingGroups(socket), config.joinEverySeconds * 1000)
      joinPendingGroups(socket)
    }
    if (connection === 'close') {
      clearInterval(joinTimer)
      const status = lastDisconnect?.error?.output?.statusCode
      if (status === DisconnectReason.loggedOut) {
        console.error(`Logged out of WhatsApp. Delete the ${config.authDir} folder and start again to log in.`)
        process.exit(1)
      }
      log(`Connection closed (${status ?? 'unknown'}); reconnecting in 5 seconds.`)
      setTimeout(start, 5000)
    }
  })

  // New messages, including the ones missed while the connector was off.
  socket.ev.on('messages.upsert', async ({ messages }) => {
    for (const message of messages) {
      await forward(socket, message).catch((error) => log('Message not forwarded:', error.message))
    }
  })

  // Someone added UniFlow's number to a group directly, or an admin approved a join request.
  socket.ev.on('groups.upsert', async (groups) => {
    for (const group of groups) {
      await reportJoined(socket, group.id, group.subject, waitingApproval.get(group.id)).catch(
        (error) => log('Join not reported:', error.message),
      )
    }
  })
}

async function forward(socket, message) {
  const data = toUniFlowMessage(message)
  if (!data) return
  let stored
  try {
    stored = await uniflow.sendMessage(data)
  } catch (error) {
    // 404: a group UniFlow doesn't know yet (e.g. joined before the backend was told).
    if (error instanceof UniFlowError && error.status === 404) return
    throw error
  }
  if (!stored.created || !data.has_files) return

  const content = normalizeMessageContent(message.message)
  const file = attachedFile(content)
  const size = Number(content[file.kind]?.fileLength ?? 0)
  if (size > config.maxFileBytes) return log('File too large, skipped.')
  const bytes = await downloadMediaMessage(message, 'buffer', {}, {
    logger: quietLogger,
    reuploadRequest: socket.updateMediaMessage,
  })
  await uniflow.sendFile(stored.id, file.fileName, file.mimeType, bytes)
}

/** Post the join notice once (unless turned off), then tell the backend UniFlow is in the group. */
async function reportJoined(socket, groupId, title, sourceId) {
  if (announced.has(groupId)) return // joining by link also fires "groups.upsert"
  announced.add(groupId)
  if (config.sendJoinNotice) await socket.sendMessage(groupId, { text: JOIN_NOTICE })
  waitingApproval.delete(groupId)
  await uniflow.joined({
    external_id: groupId,
    title: title ?? '',
    source_id: sourceId ?? null,
    notice_sent: config.sendJoinNotice,
  })
  log(`Joined "${title}".`)
}

let joining = false

/** Join the groups students added: at most one per round, and each link at most once an hour. */
async function joinPendingGroups(socket) {
  if (joining) return
  joining = true
  try {
    const pending = await uniflow.pendingSources()
    const hourAgo = Date.now() - 60 * 60 * 1000
    const next = pending.find((source) => (lastTried.get(source.id) ?? 0) < hourAgo)
    if (!next) return
    lastTried.set(next.id, Date.now())

    const code = inviteCode(next.invite_url)
    if (!code) return log(`Not a WhatsApp invite link (group ${next.id}).`)
    const info = await socket.groupGetInviteInfo(code) // the group's id and name
    waitingApproval.set(info.id, next.id)
    const joinedId = await socket.groupAcceptInvite(code)
    if (joinedId) {
      await reportJoined(socket, joinedId, info.subject, next.id)
    } else {
      log(`Asked to join "${info.subject}"; waiting for a group admin to approve.`)
    }
  } catch (error) {
    log('Joining a group failed (will try again later):', error.message)
  } finally {
    joining = false
  }
}

start()
