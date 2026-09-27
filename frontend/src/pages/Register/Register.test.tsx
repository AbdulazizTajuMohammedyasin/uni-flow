import { fireEvent, render, screen } from '@testing-library/react'
import { createMemoryRouter, RouterProvider } from 'react-router'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import * as authApi from '@/api/auth'
import { ApiError } from '@/api/errors'
import { AuthProvider } from '@/context/AuthContext'

import { RegisterPage } from './Register'

vi.mock('@/api/auth', () => ({
  restoreSession: vi.fn(),
  getCurrentUser: vi.fn(),
  login: vi.fn(),
  logout: vi.fn(),
  register: vi.fn(),
}))

function renderRegister() {
  const router = createMemoryRouter([{ path: '/register', element: <RegisterPage /> }], {
    initialEntries: ['/register'],
  })
  render(
    <AuthProvider>
      <RouterProvider router={router} />
    </AuthProvider>,
  )
}

function fill(label: string, value: string) {
  fireEvent.change(screen.getByLabelText(label), { target: { value } })
}

async function fillForm(overrides: Partial<Record<string, string>> = {}) {
  await screen.findByRole('button', { name: 'Create account' })
  const values = {
    'Full name': 'Ali Hassan',
    'Student email': 'ali@student.aiu.edu.my',
    Password: 'Str0ng-pass-99',
    'Confirm password': 'Str0ng-pass-99',
    ...overrides,
  }
  for (const [label, value] of Object.entries(values)) fill(label, value)
  fireEvent.click(screen.getByRole('button', { name: 'Create account' }))
}

beforeEach(() => {
  vi.mocked(authApi.restoreSession).mockResolvedValue(false)
  vi.mocked(authApi.register).mockReset()
})

describe('Register page', () => {
  it('only accepts AIU student emails', async () => {
    renderRegister()
    await fillForm({ 'Student email': 'ali@gmail.com' })

    expect(await screen.findByText('Use your AIU student email (@student.aiu.edu.my).')).toBeTruthy()
    expect(authApi.register).not.toHaveBeenCalled()
  })

  it('checks that the passwords match', async () => {
    renderRegister()
    await fillForm({ 'Confirm password': 'something-else' })

    expect(await screen.findByText('The passwords do not match.')).toBeTruthy()
    expect(authApi.register).not.toHaveBeenCalled()
  })

  it('tells the student to check their email after registering', async () => {
    vi.mocked(authApi.register).mockResolvedValue()
    renderRegister()
    await fillForm()

    expect(await screen.findByRole('heading', { name: 'Check your email' })).toBeTruthy()
    expect(screen.getByText('ali@student.aiu.edu.my')).toBeTruthy()
    expect(authApi.register).toHaveBeenCalledWith({
      full_name: 'Ali Hassan',
      email: 'ali@student.aiu.edu.my',
      password: 'Str0ng-pass-99',
      re_password: 'Str0ng-pass-99',
    })
  })

  it("shows the backend's message under the right field", async () => {
    vi.mocked(authApi.register).mockRejectedValue(
      new ApiError({
        status: 400,
        code: 'validation_error',
        message: 'Invalid input.',
        fields: { email: ['user with this email address already exists.'] },
      }),
    )
    renderRegister()
    await fillForm()

    expect(await screen.findByText('user with this email address already exists.')).toBeTruthy()
  })
})
