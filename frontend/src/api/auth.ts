import type { LoginData, RegisterData, User } from '@/types/auth'

import { api, refreshAccessToken } from './client'
import { toApiError } from './errors'
import { tokenStore } from './tokenStore'

/** Register: creates an inactive account and emails an activation link. */
export async function register(data: RegisterData): Promise<void> {
  try {
    await api.post('/auth/users/', data)
  } catch (error) {
    throw toApiError(error)
  }
}

/** Log in: the access token is kept in memory; the backend sets the refresh-token cookie. */
export async function login(data: LoginData): Promise<void> {
  try {
    const response = await api.post<{ access: string }>('/auth/jwt/create/', data)
    tokenStore.set(response.data.access)
  } catch (error) {
    throw toApiError(error)
  }
}

/** Log out: the backend cancels the refresh token and deletes the cookie. */
export async function logout(): Promise<void> {
  try {
    await api.post('/auth/jwt/logout/')
  } finally {
    tokenStore.clear()
  }
}

/** On page load: get an access token from the refresh-token cookie, if there is one. */
export async function restoreSession(): Promise<boolean> {
  return (await refreshAccessToken()) !== null
}

export async function getCurrentUser(): Promise<User> {
  try {
    const response = await api.get<User>('/auth/users/me/')
    return response.data
  } catch (error) {
    throw toApiError(error)
  }
}
