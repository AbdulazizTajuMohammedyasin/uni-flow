import { AxiosError, AxiosHeaders } from 'axios'
import { describe, expect, it } from 'vitest'

import { ApiError, toApiError } from './errors'

/** Build an AxiosError the way axios does for an HTTP error response. */
function httpError(status: number, data: unknown): AxiosError {
  const config = { headers: new AxiosHeaders() }
  return new AxiosError('Request failed', 'ERR_BAD_RESPONSE', config, null, {
    status,
    statusText: '',
    headers: {},
    config,
    data,
  })
}

describe('toApiError', () => {
  it('reads a validation error envelope, including field messages', () => {
    const error = toApiError(
      httpError(400, {
        error: {
          code: 'validation_error',
          message: 'Invalid input.',
          fields: { title: ['This field is required.'] },
        },
      }),
    )

    expect(error).toBeInstanceOf(ApiError)
    expect(error.status).toBe(400)
    expect(error.code).toBe('validation_error')
    expect(error.message).toBe('Invalid input.')
    expect(error.fields).toEqual({ title: ['This field is required.'] })
  })

  it('reads a non-validation envelope (fields empty)', () => {
    const error = toApiError(
      httpError(404, { error: { code: 'not_found', message: 'Not found.', fields: {} } }),
    )

    expect(error.status).toBe(404)
    expect(error.code).toBe('not_found')
    expect(error.fields).toEqual({})
  })

  it('turns "no response" into a network error', () => {
    const noResponse = new AxiosError('Network Error', 'ERR_NETWORK')
    const error = toApiError(noResponse)

    expect(error.status).toBeNull()
    expect(error.code).toBe('network_error')
  })

  it('handles an HTTP error without our envelope (e.g. an HTML 500 page)', () => {
    const error = toApiError(httpError(500, '<html>Server Error</html>'))

    expect(error.status).toBe(500)
    expect(error.code).toBe('unexpected_response')
    expect(error.message).toContain('500')
  })

  it('wraps non-HTTP errors and passes ApiError through unchanged', () => {
    expect(toApiError(new Error('boom')).code).toBe('unknown_error')

    const original = new ApiError({ status: 403, code: 'permission_denied', message: 'No.' })
    expect(toApiError(original)).toBe(original)
  })
})
