import { fireEvent, render, screen } from '@testing-library/react'
import { createMemoryRouter, RouterProvider } from 'react-router'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import * as authApi from '@/api/auth'
import { ApiError } from '@/api/errors'
import { AuthProvider } from '@/context/AuthContext'
import type { User } from '@/types/auth'

import { LoginPage } from './Login'

vi.mock('@/api/auth', () => ({
  restoreSession: vi.fn(),
  getCurrentUser: vi.fn(),
  login: vi.fn(),
  logout: vi.fn(),
  register: vi.fn(),
}))

const student = { id: 1, email: 'ali@student.aiu.edu.my', full_name: 'Ali' } as User

function renderLogin(path = '/login') {
  const router = createMemoryRouter(
    [
      { path: '/login', element: <LoginPage /> },
      { path: '/', element: <h1>Home</h1> },
      { path: '/events', element: <h1>Events</h1> },
    ],
    { initialEntries: [path] },
  )
  render(
    <AuthProvider>
      <RouterProvider router={router} />
    </AuthProvider>,
  )
  return router
}

function fill(label: string, value: string) {
  fireEvent.change(screen.getByLabelText(label), { target: { value } })
}

beforeEach(() => {
  vi.mocked(authApi.restoreSession).mockResolvedValue(false)
  vi.mocked(authApi.getCurrentUser).mockResolvedValue(student)
})

describe('Login page', () => {
  it('checks the fields before sending anything', async () => {
    renderLogin()
    fireEvent.click(await screen.findByRole('button', { name: 'Log in' }))

    expect(await screen.findByText('Enter a valid email address.')).toBeTruthy()
    expect(screen.getByText('Enter your password.')).toBeTruthy()
    expect(authApi.login).not.toHaveBeenCalled()
  })

  it('logs in and goes to the page the user wanted', async () => {
    vi.mocked(authApi.login).mockResolvedValue()
    renderLogin('/login?next=%2Fevents')

    fill('Email', 'ali@student.aiu.edu.my')
    fill('Password', 'Str0ng-pass-99')
    fireEvent.click(screen.getByRole('button', { name: 'Log in' }))

    expect(await screen.findByRole('heading', { name: 'Events' })).toBeTruthy()
    expect(authApi.login).toHaveBeenCalledWith({
      email: 'ali@student.aiu.edu.my',
      password: 'Str0ng-pass-99',
    })
  })

  it('never follows ?next= to another website', async () => {
    vi.mocked(authApi.login).mockResolvedValue()
    renderLogin('/login?next=%2F%2Fevil.example')

    fill('Email', 'ali@student.aiu.edu.my')
    fill('Password', 'Str0ng-pass-99')
    fireEvent.click(screen.getByRole('button', { name: 'Log in' }))

    expect(await screen.findByRole('heading', { name: 'Home' })).toBeTruthy()
  })

  it('explains a failed login', async () => {
    vi.mocked(authApi.login).mockRejectedValue(
      new ApiError({ status: 401, code: 'no_active_account', message: 'No active account' }),
    )
    renderLogin()

    fill('Email', 'ali@student.aiu.edu.my')
    fill('Password', 'wrong')
    fireEvent.click(screen.getByRole('button', { name: 'Log in' }))

    expect((await screen.findByRole('alert')).textContent).toContain('Wrong email or password')
  })
})
