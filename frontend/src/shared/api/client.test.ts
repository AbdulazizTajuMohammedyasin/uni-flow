import type { InternalAxiosRequestConfig } from 'axios'
import { AxiosHeaders } from 'axios'
import { afterEach, describe, expect, it } from 'vitest'

import { api } from './client'
import { tokenStore } from './tokenStore'

/** Run the request interceptors on a blank request config and return the result. */
async function runRequestInterceptors(): Promise<InternalAxiosRequestConfig> {
  let config: InternalAxiosRequestConfig = { headers: new AxiosHeaders() }
  // axios keeps registered interceptors in `handlers`; run each one in order.
  const handlers = (
    api.interceptors.request as unknown as {
      handlers: Array<{ fulfilled: (c: InternalAxiosRequestConfig) => InternalAxiosRequestConfig }>
    }
  ).handlers
  for (const handler of handlers) {
    config = await handler.fulfilled(config)
  }
  return config
}

afterEach(() => tokenStore.clear())

describe('api client', () => {
  it('points at the API and identifies itself as the web client', () => {
    expect(api.defaults.baseURL).toBe('http://localhost:8000/api/v1')
    expect(api.defaults.withCredentials).toBe(true)
    expect(api.defaults.headers['X-Client']).toBe('web')
  })

  it('adds no Authorization header when logged out', async () => {
    const config = await runRequestInterceptors()
    expect(config.headers.Authorization).toBeUndefined()
  })

  it('adds the Bearer token when logged in', async () => {
    tokenStore.set('abc.def.ghi')
    const config = await runRequestInterceptors()
    expect(config.headers.Authorization).toBe('Bearer abc.def.ghi')
  })
})
