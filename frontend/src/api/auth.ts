import type { ChangePasswordData, LoginData, RegisterData, UpdateMeData, User } from '@/types/auth'

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

/** Activate an account with the uid/token from the activation email link. */
export async function activateAccount(uid: string, token: string): Promise<void> {
  try {
    await api.post('/auth/users/activation/', { uid, token })
  } catch (error) {
    throw toApiError(error)
  }
}

/** Send the activation email again. */
export async function resendActivation(email: string): Promise<void> {
  try {
    await api.post('/auth/users/resend_activation/', { email })
  } catch (error) {
    throw toApiError(error)
  }
}

/** Email a password-reset link (same answer whether or not the email exists). */
export async function requestPasswordReset(email: string): Promise<void> {
  try {
    await api.post('/auth/users/reset_password/', { email })
  } catch (error) {
    throw toApiError(error)
  }
}

/** Set a new password with the uid/token from the reset email link. */
export async function confirmPasswordReset(data: {
  uid: string
  token: string
  new_password: string
  re_new_password: string
}): Promise<void> {
  try {
    await api.post('/auth/users/reset_password_confirm/', data)
  } catch (error) {
    throw toApiError(error)
  }
}

/** Update your own details (name, student profile). Returns the updated user. */
export async function updateCurrentUser(data: UpdateMeData): Promise<User> {
  try {
    return (await api.patch<User>('/auth/users/me/', data)).data
  } catch (error) {
    throw toApiError(error)
  }
}

/** Change your password (needs the current one). */
export async function changePassword(data: ChangePasswordData): Promise<void> {
  try {
    await api.post('/auth/users/set_password/', data)
  } catch (error) {
    throw toApiError(error)
  }
}
