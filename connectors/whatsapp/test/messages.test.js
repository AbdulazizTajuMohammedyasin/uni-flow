import assert from 'node:assert/strict'
import { test } from 'node:test'

import { attachedFile, inviteCode, JOIN_NOTICE, toUniFlowMessage } from '../src/messages.js'

const GROUP = '120363000000000001@g.us'
const SENT = 1790000000

function whatsapp(message, key = {}) {
  return {
    key: { remoteJid: GROUP, id: 'ABC1', participant: '123456789@lid', fromMe: false, ...key },
    pushName: 'Dr Lee',
    messageTimestamp: SENT,
    message,
  }
}

test('a text message in a group', () => {
  assert.deepEqual(toUniFlowMessage(whatsapp({ conversation: 'Class moves to 2pm' })), {
    source_external_id: GROUP,
    message_id: 'ABC1',
    sender_ref: '123456789@lid',
    sender_name: 'Dr Lee',
    text: 'Class moves to 2pm',
    sent_at: new Date(SENT * 1000).toISOString(),
    reply_to: null,
    has_files: false,
  })
})

test('a reply, and the private sender id is preferred over the phone number', () => {
  const message = whatsapp(
    { extendedTextMessage: { text: 'Same room?', contextInfo: { stanzaId: 'ABC0' } } },
    { participant: '60123456789@s.whatsapp.net', participantAlt: '987@lid' },
  )
  const result = toUniFlowMessage(message)
  assert.equal(result.text, 'Same room?')
  assert.equal(result.reply_to, 'ABC0')
  assert.equal(result.sender_ref, '987@lid')
})

test('a timestamp given as a "Long" object', () => {
  const message = whatsapp({ conversation: 'hi' })
  message.messageTimestamp = { toNumber: () => SENT }
  assert.equal(toUniFlowMessage(message).sent_at, new Date(SENT * 1000).toISOString())
})

test('a PDF with a caption, and a photo without one', () => {
  const pdf = whatsapp({
    documentMessage: { mimetype: 'application/pdf', fileName: 'timetable.pdf', caption: 'New timetable' },
  })
  assert.equal(toUniFlowMessage(pdf).text, 'New timetable')
  assert.equal(toUniFlowMessage(pdf).has_files, true)
  assert.deepEqual(attachedFile(pdf.message), {
    kind: 'documentMessage',
    mimeType: 'application/pdf',
    fileName: 'timetable.pdf',
  })

  const photo = whatsapp({ imageMessage: { mimetype: 'image/jpeg' } })
  assert.equal(toUniFlowMessage(photo).text, '')
  assert.equal(toUniFlowMessage(photo).has_files, true)
})

test('ignored: private chats, status updates, own messages, stickers and other files', () => {
  const text = { conversation: 'hello' }
  assert.equal(toUniFlowMessage(whatsapp(text, { remoteJid: '60123@s.whatsapp.net' })), null)
  assert.equal(toUniFlowMessage(whatsapp(text, { remoteJid: 'status@broadcast' })), null)
  assert.equal(toUniFlowMessage(whatsapp(text, { fromMe: true })), null)
  assert.equal(toUniFlowMessage(whatsapp({ stickerMessage: {} })), null)
  assert.equal(toUniFlowMessage(whatsapp({ documentMessage: { mimetype: 'application/zip' } })), null)
})

test('invite links', () => {
  assert.equal(inviteCode('https://chat.whatsapp.com/AbCd123XyZ'), 'AbCd123XyZ')
  assert.equal(inviteCode(' https://chat.whatsapp.com/invite/AbCd123/ '), 'AbCd123')
  assert.equal(inviteCode('https://evil.example.com/AbCd123'), null)
  assert.equal(inviteCode('http://chat.whatsapp.com/AbCd123'), null)
})

test('the join notice says what UniFlow does and how to remove it', () => {
  assert.match(JOIN_NOTICE, /only reads/)
  assert.match(JOIN_NOTICE, /remove this number/)
})
