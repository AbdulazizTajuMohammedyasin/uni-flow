import { fireEvent, render, screen } from '@testing-library/react'
import { StrictMode } from 'react'
import { createMemoryRouter, RouterProvider } from 'react-router'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import * as authApi from '@/api/auth'
import { ApiError } from '@/api/errors'

import { ActivateAccountPage } from './ActivateAccount'

vi.mock('@/api/auth', () => ({ activateAccount: vi.fn(), resendActivation: vi.fn() }))

function renderAt(path = '/verify-email/MQ/abc-123') {
  const router = createMemoryRouter(
    [{ path: '/verify-email/:uid/:token', element: <ActivateAccountPage /> }],
    { initialEntries: [path] },
  )
  // StrictMode runs effects twice, like development does.
  render(
    <StrictMode>
      <RouterProvider router={router} />
    </StrictMode>,
  )
}

beforeEach(() => {
  vi.mocked(authApi.activateAccount).mockReset()
  vi.mocked(authApi.resendActivation).mockReset()
})

describe('Activate account page', () => {
  it('activates once with the uid and token from the link', async () => {
    vi.mocked(authApi.activateAccount).mockResolvedValue()
    renderAt()

    expect(await screen.findByRole('heading', { name: 'Your account is active' })).toBeTruthy()
    expect(authApi.activateAccount).toHaveBeenCalledTimes(1)
    expect(authApi.activateAccount).toHaveBeenCalledWith('MQ', 'abc-123')
    expect(screen.getByRole('link', { name: 'Log in' }).getAttribute('href')).toBe('/login')
  })

  it('treats an already-used link as already activated', async () => {
    vi.mocked(authApi.activateAccount).mockRejectedValue(
      new ApiError({ status: 403, code: 'permission_denied', message: 'Stale token' }),
    )
    renderAt()

    expect(await screen.findByRole('heading', { name: 'Account already activated' })).toBeTruthy()
  })

  it('offers a new activation email when the link is invalid', async () => {
    vi.mocked(authApi.activateAccount).mockRejectedValue(
      new ApiError({ status: 400, code: 'validation_error', message: 'Invalid input.' }),
    )
    vi.mocked(authApi.resendActivation).mockResolvedValue()
    renderAt()

    expect(await screen.findByRole('heading', { name: "This link didn't work" })).toBeTruthy()
    fireEvent.change(screen.getByLabelText('Student email'), {
      target: { value: 'ali@student.aiu.edu.my' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Send a new activation link' }))

    expect(await screen.findByText(/a new link is on its way/)).toBeTruthy()
    expect(authApi.resendActivation).toHaveBeenCalledWith('ali@student.aiu.edu.my')
  })
})
