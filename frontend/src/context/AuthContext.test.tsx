import { fireEvent, render, screen } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import * as authApi from '@/api/auth'
import { capabilitiesOf } from '@/test/fixtures'
import type { User } from '@/types/auth'

import { AuthProvider, useAuth } from './AuthContext'

vi.mock('@/api/auth', () => ({
  restoreSession: vi.fn(),
  getCurrentUser: vi.fn(),
  login: vi.fn(),
  logout: vi.fn(),
}))

const student: User = {
  id: 1,
  email: 'ali@student.aiu.edu.my',
  full_name: 'Ali Hassan',
  role: 'student',
  profile_complete: false,
  student_profile: { student_number: null, school: null, programme: null, intake: null },
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
