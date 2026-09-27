import { QueryClientProvider } from '@tanstack/react-query'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { createMemoryRouter, RouterProvider } from 'react-router'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import * as academicsApi from '@/api/academics'
import * as authApi from '@/api/auth'
import { AuthProvider } from '@/context/AuthContext'
import { createQueryClient } from '@/lib/queryClient'
import { intakes, makeStudent, programmes, schools } from '@/test/fixtures'

import { ProfilePage } from './Profile'

vi.mock('@/api/auth', () => ({
  restoreSession: vi.fn(),
  getCurrentUser: vi.fn(),
  updateCurrentUser: vi.fn(),
  changePassword: vi.fn(),
  login: vi.fn(),
  logout: vi.fn(),
}))
vi.mock('@/api/academics', () => ({
  getSchools: vi.fn(),
  getProgrammes: vi.fn(),
  getIntakes: vi.fn(),
}))

const completeStudent = makeStudent({
  profile_complete: true,
  student_profile: { student_number: 'AIU22001', school: 1, programme: 10, intake: 100 },
})

function renderProfile() {
  const router = createMemoryRouter(
    [
      { path: '/profile', element: <ProfilePage /> },
      { path: '/login', element: <h1>Log in</h1> },
    ],
    { initialEntries: ['/profile'] },
  )
  render(
    <QueryClientProvider client={createQueryClient()}>
      <AuthProvider>
        <RouterProvider router={router} />
      </AuthProvider>
    </QueryClientProvider>,
  )
}

beforeEach(() => {
  vi.mocked(authApi.restoreSession).mockResolvedValue(true)
  vi.mocked(authApi.getCurrentUser).mockResolvedValue(completeStudent)
  vi.mocked(authApi.logout).mockResolvedValue()
  vi.mocked(academicsApi.getSchools).mockResolvedValue(schools)
  vi.mocked(academicsApi.getIntakes).mockResolvedValue(intakes)
  vi.mocked(academicsApi.getProgrammes).mockImplementation(async (schoolId) =>
    programmes.filter((p) => p.school === schoolId),
  )
})

describe('Profile page', () => {
  it('shows the account and pre-fills the saved studies', async () => {
    renderProfile()

    expect(await screen.findByText('ali@student.aiu.edu.my')).toBeTruthy()
    expect(screen.getByText('Student')).toBeTruthy()
    await waitFor(() => {
      expect((screen.getByLabelText('School') as HTMLSelectElement).value).toBe('1')
      expect((screen.getByLabelText('Programme') as HTMLSelectElement).value).toBe('10')
      expect((screen.getByLabelText('Intake') as HTMLSelectElement).value).toBe('100')
    })
    expect((screen.getByLabelText('Student number (optional)') as HTMLInputElement).value).toBe(
      'AIU22001',
    )
  })

  it('changes the password', async () => {
    vi.mocked(authApi.changePassword).mockResolvedValue()
    renderProfile()

    fireEvent.change(await screen.findByLabelText('Current password'), { target: { value: 'Old-pass-123' } })
    fireEvent.change(screen.getByLabelText('New password'), { target: { value: 'N3w-strong-pass-77' } })
    fireEvent.change(screen.getByLabelText('Confirm new password'), {
      target: { value: 'N3w-strong-pass-77' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Change password' }))

    expect(await screen.findByText('Password changed.')).toBeTruthy()
    expect(authApi.changePassword).toHaveBeenCalledWith({
      current_password: 'Old-pass-123',
      new_password: 'N3w-strong-pass-77',
      re_new_password: 'N3w-strong-pass-77',
    })
  })

  it('logs out and goes to the login page', async () => {
    renderProfile()

    fireEvent.click(await screen.findByRole('button', { name: 'Log out' }))

    expect(await screen.findByRole('heading', { name: 'Log in' })).toBeTruthy()
    expect(authApi.logout).toHaveBeenCalledOnce()
  })
})
