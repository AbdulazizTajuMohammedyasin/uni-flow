import { isAxiosError } from 'axios'

/** Field name → list of messages, e.g. { title: ["This field is required."] } */
export type FieldErrors = Record<string, string[]>

/**
 * A normalized API error. The backend always answers errors as
 * { "error": { "code", "message", "fields" } } (docs/04-api.md); this class turns that,
 * network failures and unexpected responses into one predictable shape for the UI.
 */
export class ApiError extends Error {
  readonly status: number | null
  readonly code: string
  readonly fields: FieldErrors

  constructor(options: { status: number | null; code: string; message: string; fields?: FieldErrors }) {
    super(options.message)
    this.name = 'ApiError'
    this.status = options.status
    this.code = options.code
    this.fields = options.fields ?? {}
  }
}

type ErrorEnvelope = {
  error: { code: string; message: string; fields?: FieldErrors }
}

function isErrorEnvelope(data: unknown): data is ErrorEnvelope {
  if (typeof data !== 'object' || data === null || !('error' in data)) return false
  const error = (data as { error: unknown }).error
  return (
    typeof error === 'object' &&
    error !== null &&
    typeof (error as { code?: unknown }).code === 'string' &&
    typeof (error as { message?: unknown }).message === 'string'
  )
}

/** Convert anything thrown by an API call into an ApiError. */
export function toApiError(error: unknown): ApiError {
  if (error instanceof ApiError) return error

  if (isAxiosError(error)) {
    if (!error.response) {
      return new ApiError({
        status: null,
        code: 'network_error',
        message: 'Cannot reach the server. Check your connection and try again.',
      })
    }

    const { status, data } = error.response
    if (isErrorEnvelope(data)) {
      return new ApiError({
        status,
        code: data.error.code,
        message: data.error.message,
        fields: data.error.fields,
      })
    }

    return new ApiError({
      status,
      code: 'unexpected_response',
      message: `The server returned an unexpected error (HTTP ${status}).`,
    })
  }

  return new ApiError({ status: null, code: 'unknown_error', message: 'Something went wrong.' })
}
