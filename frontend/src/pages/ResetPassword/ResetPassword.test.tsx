import { fireEvent, render, screen } from '@testing-library/react'
import { createMemoryRouter, RouterProvider } from 'react-router'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import * as authApi from '@/api/auth'
import { ApiError } from '@/api/errors'

import { ResetPasswordPage } from './ResetPassword'

vi.mock('@/api/auth', () => ({ confirmPasswordReset: vi.fn() }))

function renderPage() {
  const router = createMemoryRouter(
    [{ path: '/reset-password/:uid/:token', element: <ResetPasswordPage /> }],
    { initialEntries: ['/reset-password/MQ/tok-1'] },
  )
  render(<RouterProvider router={router} />)
}

async function submit(password: string, again = password) {
  fireEvent.change(await screen.findByLabelText('New password'), { target: { value: password } })
  fireEvent.change(screen.getByLabelText('Confirm new password'), { target: { value: again } })
  fireEvent.click(screen.getByRole('button', { name: 'Save new password' }))
}

beforeEach(() => {
  vi.mocked(authApi.confirmPasswordReset).mockReset()
})

describe('Reset password page', () => {
  it('saves the new password with the uid and token from the link', async () => {
    vi.mocked(authApi.confirmPasswordReset).mockResolvedValue()
    renderPage()
    await submit('N3w-strong-pass-77')

    expect(await screen.findByRole('heading', { name: 'Password changed' })).toBeTruthy()
    expect(authApi.confirmPasswordReset).toHaveBeenCalledWith({
      uid: 'MQ',
      token: 'tok-1',
      new_password: 'N3w-strong-pass-77',
      re_new_password: 'N3w-strong-pass-77',
    })
  })

  it('checks that the passwords match', async () => {
    renderPage()
    await submit('N3w-strong-pass-77', 'different')

    expect(await screen.findByText('The passwords do not match.')).toBeTruthy()
    expect(authApi.confirmPasswordReset).not.toHaveBeenCalled()
  })

  it('explains an invalid or used link', async () => {
    vi.mocked(authApi.confirmPasswordReset).mockRejectedValue(
      new ApiError({
        status: 400,
        code: 'validation_error',
        message: 'Invalid input.',
        fields: { token: ['Invalid token for given user.'] },
      }),
    )
    renderPage()
    await submit('N3w-strong-pass-77')

    expect((await screen.findByRole('alert')).textContent).toContain('invalid or has already been used')
  })
})
