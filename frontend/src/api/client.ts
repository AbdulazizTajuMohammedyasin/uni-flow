import axios, { type AxiosError, type InternalAxiosRequestConfig } from 'axios'

import { tokenStore } from './tokenStore'

const baseURL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000/api/v1'

/**
 * The one HTTP client for the Django API (`/api/v1/`).
 * - Adds `Authorization: Bearer <access token>` when logged in.
 * - On a 401 it gets a new access token once (the browser sends the httpOnly
 *   refresh-token cookie) and repeats the request.
 * `withCredentials` lets the browser send and receive that cookie.
 */
export const api = axios.create({ baseURL, withCredentials: true })

api.interceptors.request.use((config) => {
  const token = tokenStore.get()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

/** Ask the backend for a new access token using the refresh-token cookie. */
export async function refreshAccessToken(): Promise<string | null> {
  try {
    const response = await axios.post<{ access: string }>(`${baseURL}/auth/jwt/refresh/`, null, {
      withCredentials: true,
    })
    tokenStore.set(response.data.access)
    return response.data.access
  } catch {
    tokenStore.clear()
    return null
  }
}

// Several requests may fail with 401 at the same moment: they share one refresh.
let refreshing: Promise<string | null> | null = null

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const original = error.config as (InternalAxiosRequestConfig & { _retry?: boolean }) | undefined
    const isAuthCall = original?.url?.startsWith('/auth/jwt/')

    if (error.response?.status !== 401 || !original || original._retry || isAuthCall) {
      return Promise.reject(error)
    }

    original._retry = true
    refreshing ??= refreshAccessToken().finally(() => {
      refreshing = null
    })
    const token = await refreshing
    if (!token) {
      return Promise.reject(error) // refresh failed: the user must log in again
    }
    original.headers.Authorization = `Bearer ${token}`
    return api(original)
  },
)
