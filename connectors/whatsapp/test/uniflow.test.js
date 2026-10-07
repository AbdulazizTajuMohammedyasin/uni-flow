import assert from 'node:assert/strict'
import { test } from 'node:test'

import { createClient, multipartFile, sign, UniFlowError } from '../src/uniflow.js'

test('signs exactly like the backend (value from apps/intelligence/connector.py sign())', () => {
  const signature = sign('s3cret', '1790000000', 'POST', '/api/v1/internal/messages/', Buffer.from('{"a": 1}'))
  assert.equal(signature, '59d800d2b6708b81894ed7c964ee8bcab1765935ca4b5123f2d3625f98f55fc7')
})

test('builds a multipart body with the file inside', () => {
  const { body, contentType } = multipartFile('file', 'time"table.pdf', 'application/pdf', Buffer.from('%PDF'))
  const boundary = contentType.split('boundary=')[1]
  const text = body.toString()
  assert.ok(text.startsWith(`--${boundary}\r\n`))
  assert.ok(text.includes('name="file"; filename="time_table.pdf"'))
  assert.ok(text.includes('\r\n\r\n%PDF\r\n'))
  assert.ok(text.endsWith(`--${boundary}--\r\n`))
})

test('sends signed requests to the internal addresses', async () => {
  const sent = []
  const fakeFetch = async (url, options) => {
    sent.push({ url: String(url), ...options })
    return new Response(JSON.stringify({ id: 7, created: true }), { status: 201 })
  }
  const client = createClient({ apiUrl: 'http://127.0.0.1:8000/api/v1', secret: 's3cret', fetchImpl: fakeFetch })

  assert.deepEqual(await client.sendMessage({ text: 'hi' }), { id: 7, created: true })

  const [request] = sent
  assert.equal(request.url, 'http://127.0.0.1:8000/api/v1/internal/messages/')
  assert.equal(request.method, 'POST')
  const timestamp = request.headers['X-UniFlow-Timestamp']
  const expected = sign('s3cret', timestamp, 'POST', '/api/v1/internal/messages/', request.body)
  assert.equal(request.headers['X-UniFlow-Signature'], expected)
  assert.ok(Math.abs(Number(timestamp) - Date.now() / 1000) < 5)
})

test('a refused request becomes an error with the status', async () => {
  const fakeFetch = async () => new Response('{"error": "no"}', { status: 404 })
  const client = createClient({ apiUrl: 'http://x/api/v1/', secret: 's', fetchImpl: fakeFetch })
  await assert.rejects(client.pendingSources(), (error) => error instanceof UniFlowError && error.status === 404)
})
