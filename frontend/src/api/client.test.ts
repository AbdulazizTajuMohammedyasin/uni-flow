import type { AxiosAdapter, InternalAxiosRequestConfig } from 'axios'
import axios, { AxiosError } from 'axios'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { api } from './client'
import { tokenStore } from './tokenStore'

/** Build a fake axios response. */
function reply(config: InternalAxiosRequestConfig, status: number, data: unknown = {}) {
  const response = { config, status, statusText: '', headers: {}, data }
  if (status >= 400) {
    return Promise.reject(new AxiosError('fail', 'ERR', config, null, response))
  }
  return Promise.resolve(response)
}

const realAdapter = api.defaults.adapter

beforeEach(() => tokenStore.clear())
afterEach(() => {
  api.defaults.adapter = realAdapter
  vi.restoreAllMocks()
})

describe('api client', () => {
  it('points at the API and sends cookies', () => {
    expect(api.defaults.baseURL).toBe('http://localhost:8000/api/v1')
    expect(api.defaults.withCredentials).toBe(true)
  })

  it('adds the access token when logged in', async () => {
    tokenStore.set('abc')
    const seen: (string | undefined)[] = []
    api.defaults.adapter = ((config) => {
      seen.push(config.headers.Authorization as string | undefined)
      return reply(config, 200)
    }) as AxiosAdapter

    await api.get('/academics/schools/')

    expect(seen).toEqual(['Bearer abc'])
  })

  it('on 401, refreshes the token once (via the cookie) and repeats the request', async () => {
    tokenStore.set('expired')
    const refresh = vi.spyOn(axios, 'post').mockResolvedValue({ data: { access: 'fresh' } })
    const seen: string[] = []
    api.defaults.adapter = ((config) => {
      seen.push(config.headers.Authorization as string)
      return reply(config, config.headers.Authorization === 'Bearer fresh' ? 200 : 401)
    }) as AxiosAdapter

    const response = await api.get('/academics/schools/')

    expect(response.status).toBe(200)
    expect(seen).toEqual(['Bearer expired', 'Bearer fresh'])
    expect(refresh).toHaveBeenCalledOnce()
    expect(refresh.mock.calls[0][0]).toContain('/auth/jwt/refresh/')
    expect(tokenStore.get()).toBe('fresh')
  })

  it('gives up when the refresh fails (the user must log in again)', async () => {
    tokenStore.set('expired')
    vi.spyOn(axios, 'post').mockRejectedValue(new Error('refresh failed'))
    api.defaults.adapter = ((config) => reply(config, 401)) as AxiosAdapter

    await expect(api.get('/academics/schools/')).rejects.toBeInstanceOf(AxiosError)
    expect(tokenStore.get()).toBeNull()
  })
})
