import { fireEvent, render, screen } from '@testing-library/react'
import { createMemoryRouter, RouterProvider } from 'react-router'
import { describe, expect, it, vi } from 'vitest'

import * as authApi from '@/api/auth'

import { ForgotPasswordPage } from './ForgotPassword'

vi.mock('@/api/auth', () => ({ requestPasswordReset: vi.fn() }))

function renderPage() {
  const router = createMemoryRouter([{ path: '/', element: <ForgotPasswordPage /> }])
  render(<RouterProvider router={router} />)
}

describe('Forgot password page', () => {
  it('sends a reset link and says to check the email', async () => {
    vi.mocked(authApi.requestPasswordReset).mockResolvedValue()
    renderPage()

    fireEvent.change(await screen.findByLabelText('Email'), {
      target: { value: 'ali@student.aiu.edu.my' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Send reset link' }))

    expect(await screen.findByRole('heading', { name: 'Check your email' })).toBeTruthy()
    expect(authApi.requestPasswordReset).toHaveBeenCalledWith('ali@student.aiu.edu.my')
  })

  it('checks the email before sending', async () => {
    renderPage()
    fireEvent.click(await screen.findByRole('button', { name: 'Send reset link' }))

    expect(await screen.findByText('Enter a valid email address.')).toBeTruthy()
  })
})
