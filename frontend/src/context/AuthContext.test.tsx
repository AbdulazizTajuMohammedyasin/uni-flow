import { act, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import * as authApi from '@/api/auth'
import * as notificationsApi from '@/api/notifications'
import { capabilitiesOf, makeSchoolStaff, makeStudentProfile } from '@/test/fixtures'
import type { User } from '@/types/auth'

import { AuthProvider, useAuth } from './AuthContext'

vi.mock('@/api/auth', () => ({
  restoreSession: vi.fn(),
  getCurrentUser: vi.fn(),
  login: vi.fn(),
  logout: vi.fn(),
}))
vi.mock('@/api/notifications', () => ({
  registerDevice: vi.fn(),
  unregisterDevice: vi.fn(),
}))

const student: User = {
  id: 1,
  email: 'ali@student.aiu.edu.my',
  full_name: 'Ali Hassan',
  role: 'student',
  profile_complete: false,
  student_profile: makeStudentProfile(),
  staff_profile: null,
  capabilities: capabilitiesOf([]),
  publishers: [],
}

/** A tiny page that shows the auth state and has log in / log out buttons. */
function Probe() {
  const auth = useAuth()
  return (
    <>
      <p>{auth.isLoading ? 'loading' : (auth.user?.email ?? 'logged out')}</p>
      <button onClick={() => auth.login({ email: 'ali@student.aiu.edu.my', password: 'x' })}>
        log in
      </button>
      <button onClick={() => auth.logout()}>log out</button>
    </>
  )
}

function renderProvider() {
  render(
    <AuthProvider>
      <Probe />
    </AuthProvider>,
  )
}

beforeEach(() => {
  vi.mocked(authApi.getCurrentUser).mockResolvedValue(student)
  vi.mocked(authApi.login).mockResolvedValue()
  vi.mocked(authApi.logout).mockResolvedValue()
})

describe('AuthProvider', () => {
  it('restores the session from the cookie on page load', async () => {
    vi.mocked(authApi.restoreSession).mockResolvedValue(true)
    renderProvider()

    expect(screen.getByText('loading')).toBeTruthy()
    expect(await screen.findByText('ali@student.aiu.edu.my')).toBeTruthy()
  })

  it('stays logged out when there is no valid cookie', async () => {
    vi.mocked(authApi.restoreSession).mockResolvedValue(false)
    renderProvider()

    expect(await screen.findByText('logged out')).toBeTruthy()
    expect(authApi.getCurrentUser).not.toHaveBeenCalled()
  })

  it('login loads the user; logout clears it', async () => {
    vi.mocked(authApi.restoreSession).mockResolvedValue(false)
    renderProvider()
    await screen.findByText('logged out')

    fireEvent.click(screen.getByRole('button', { name: 'log in' }))
    expect(await screen.findByText('ali@student.aiu.edu.my')).toBeTruthy()

    fireEvent.click(screen.getByRole('button', { name: 'log out' }))
    expect(await screen.findByText('logged out')).toBeTruthy()
    expect(authApi.logout).toHaveBeenCalledOnce()
  })
})

describe('inside the UniFlow phone app', () => {
  const TOKEN = 'ExponentPushToken[ali-phone]'
  let told: Record<string, unknown>[]

  /** What the app puts on the page: its details, and a way to receive messages. */
  function openInApp(pushToken: string | null = TOKEN) {
    window.UniFlowApp = { bridgeVersion: 1, platform: 'android', appVersion: '1.0.0', pushToken }
    window.ReactNativeWebView = { postMessage: (message) => told.push(JSON.parse(message)) }
  }

  beforeEach(() => {
    told = []
    vi.mocked(notificationsApi.registerDevice).mockResolvedValue()
    vi.mocked(notificationsApi.unregisterDevice).mockResolvedValue()
  })

  afterEach(() => {
    delete window.UniFlowApp
    delete window.ReactNativeWebView
  })

  it('registers the phone once a student is logged in, once per page load', async () => {
    openInApp()
    vi.mocked(authApi.restoreSession).mockResolvedValue(true)
    renderProvider()

    await waitFor(() => expect(told).toContainEqual({ v: 1, type: 'push-registration', status: 'registered' }))
    expect(notificationsApi.registerDevice).toHaveBeenCalledExactlyOnceWith({
      token: TOKEN,
      platform: 'android',
      app_version: '1.0.0',
    })
    expect(told[0]).toEqual({ v: 1, type: 'session', signedIn: true })

    act(() => window.dispatchEvent(new CustomEvent('uniflow:push-token', { detail: { token: TOKEN } })))
    expect(notificationsApi.registerDevice).toHaveBeenCalledOnce() // the same address: not again
  })

  it('registers a push address the app announces later', async () => {
    openInApp(null) // notifications not allowed yet
    vi.mocked(authApi.restoreSession).mockResolvedValue(true)
    renderProvider()
    await screen.findByText('ali@student.aiu.edu.my')
    expect(notificationsApi.registerDevice).not.toHaveBeenCalled()

    act(() => {
      window.UniFlowApp!.pushToken = TOKEN
      window.dispatchEvent(new CustomEvent('uniflow:push-token', { detail: { token: TOKEN, platform: 'android' } }))
    })

    await waitFor(() => expect(notificationsApi.registerDevice).toHaveBeenCalledOnce())
  })

  it('tells the app when registering fails', async () => {
    openInApp()
    vi.mocked(notificationsApi.registerDevice).mockRejectedValue(new Error('offline'))
    vi.mocked(authApi.restoreSession).mockResolvedValue(true)
    renderProvider()

    await waitFor(() => expect(told).toContainEqual({ v: 1, type: 'push-registration', status: 'failed' }))
  })

  it('registers nothing for staff, or when logged out', async () => {
    openInApp()
    vi.mocked(authApi.restoreSession).mockResolvedValue(false)
    renderProvider()
    await screen.findByText('logged out')
    expect(told).toEqual([{ v: 1, type: 'session', signedIn: false }])

    vi.mocked(authApi.getCurrentUser).mockResolvedValue(makeSchoolStaff())
    fireEvent.click(screen.getByRole('button', { name: 'log in' }))
    await waitFor(() => expect(told).toContainEqual({ v: 1, type: 'session', signedIn: true }))
    expect(notificationsApi.registerDevice).not.toHaveBeenCalled()
  })

  it('unregisters the phone before logging out, and logs out even if that fails', async () => {
    openInApp()
    vi.mocked(notificationsApi.unregisterDevice).mockRejectedValue(new Error('offline'))
    vi.mocked(authApi.logout).mockImplementation(async () => {
      expect(notificationsApi.unregisterDevice).toHaveBeenCalledWith(TOKEN) // first
    })
    vi.mocked(authApi.restoreSession).mockResolvedValue(true)
    renderProvider()
    await screen.findByText('ali@student.aiu.edu.my')

    fireEvent.click(screen.getByRole('button', { name: 'log out' }))

    expect(await screen.findByText('logged out')).toBeTruthy()
    expect(authApi.logout).toHaveBeenCalledOnce()
    expect(told).toContainEqual({ v: 1, type: 'push-registration', status: 'unregistered' })
    expect(told.at(-1)).toEqual({ v: 1, type: 'session', signedIn: false })
  })
})

describe('in an ordinary browser', () => {
  it('never registers a phone or unregisters on logout', async () => {
    vi.mocked(authApi.restoreSession).mockResolvedValue(true)
    renderProvider()
    await screen.findByText('ali@student.aiu.edu.my')

    fireEvent.click(screen.getByRole('button', { name: 'log out' }))

    expect(await screen.findByText('logged out')).toBeTruthy()
    expect(notificationsApi.registerDevice).not.toHaveBeenCalled()
    expect(notificationsApi.unregisterDevice).not.toHaveBeenCalled()
  })
})
