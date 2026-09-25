import axios from 'axios'

import { tokenStore } from './tokenStore'

/**
 * The one HTTP client for talking to the Django API (`/api/v1/`).
 * - `withCredentials` lets the browser send the httpOnly refresh-token cookie (from M1.6).
 * - `X-Client: web` tells the backend this is the web app (the future mobile app omits it).
 * The automatic "refresh the token on 401 and retry" logic is added in M1.9.
 */
export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? 'http://localhost:8000/api/v1',
  withCredentials: true,
  headers: { 'X-Client': 'web' },
})

// Attach the access token (when logged in) to every request.
api.interceptors.request.use((config) => {
  const token = tokenStore.get()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})
