// Talking to the UniFlow backend's private addresses (/api/v1/internal/, M6.2).
// Every request is signed exactly like backend/apps/intelligence/connector.py expects:
//   X-UniFlow-Timestamp: Unix time in seconds
//   X-UniFlow-Signature: hex HMAC-SHA256 of "<timestamp>.<METHOD>.<path>.<body>"
import { createHmac, randomBytes } from 'node:crypto'

/** The signature for one request (the backend computes the same and compares). */
export function sign(secret, timestamp, method, path, body) {
  const head = Buffer.from(`${timestamp}.${method.toUpperCase()}.${path}.`)
  return createHmac('sha256', secret).update(Buffer.concat([head, body])).digest('hex')
}

/** A multipart/form-data body with one file, built by hand so its exact bytes can be signed. */
export function multipartFile(field, fileName, contentType, data) {
  const boundary = `uniflow${randomBytes(12).toString('hex')}`
  const safeName = fileName.replace(/["\r\n]/g, '_')
  const head =
    `--${boundary}\r\n` +
    `Content-Disposition: form-data; name="${field}"; filename="${safeName}"\r\n` +
    `Content-Type: ${contentType}\r\n\r\n`
  const body = Buffer.concat([Buffer.from(head), data, Buffer.from(`\r\n--${boundary}--\r\n`)])
  return { body, contentType: `multipart/form-data; boundary=${boundary}` }
}

export class UniFlowError extends Error {
  constructor(status, message) {
    super(message)
    this.status = status
  }
}

/** The backend's private addresses. `apiUrl` is e.g. http://127.0.0.1:8000/api/v1 */
export function createClient({ apiUrl, secret, fetchImpl = fetch }) {
  const base = new URL(apiUrl.endsWith('/') ? apiUrl : `${apiUrl}/`)

  async function request(method, address, body = Buffer.alloc(0), contentType = 'application/json') {
    const url = new URL(`internal/${address}`, base)
    const timestamp = String(Math.floor(Date.now() / 1000))
    const headers = {
      'X-UniFlow-Timestamp': timestamp,
      'X-UniFlow-Signature': sign(secret, timestamp, method, url.pathname, body),
    }
    if (method !== 'GET') headers['Content-Type'] = contentType
    const response = await fetchImpl(url, {
      method,
      headers,
      body: method === 'GET' ? undefined : body,
    })
    const text = await response.text()
    if (!response.ok) throw new UniFlowError(response.status, `${method} ${url.pathname}: ${response.status} ${text}`)
    return text ? JSON.parse(text) : null
  }

  const json = (method, address, data) => request(method, address, Buffer.from(JSON.stringify(data)))

  return {
    /** Groups students added that UniFlow's number should join: [{id, title, invite_url}]. */
    pendingSources: () => request('GET', 'sources/pending/'),
    /** UniFlow's number is in a group now. */
    joined: (data) => json('POST', 'sources/joined/', data),
    /** A new group message: {id, created}. Sending it again changes nothing. */
    sendMessage: (data) => json('POST', 'messages/', data),
    /** A file of a message stored with sendMessage. */
    sendFile: (messageId, fileName, contentType, data) => {
      const { body, contentType: type } = multipartFile('file', fileName, contentType, data)
      return request('POST', `messages/${messageId}/files/`, body, type)
    },
  }
}
