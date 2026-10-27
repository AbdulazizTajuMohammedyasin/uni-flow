import { QueryClientProvider } from '@tanstack/react-query'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { createMemoryRouter, RouterProvider } from 'react-router'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import * as academicsApi from '@/api/academics'
import * as authApi from '@/api/auth'
import * as notificationsApi from '@/api/notifications'
import { AuthProvider } from '@/context/AuthContext'
import { createQueryClient } from '@/lib/queryClient'
import {
  intakes,
  makeStudent,
  makeStudentProfile,
  preferenceChoices,
  programmes,
  schools,
} from '@/test/fixtures'

import { ProfilePage } from './Profile'

vi.mock('@/api/auth', () => ({
  restoreSession: vi.fn(),
  getCurrentUser: vi.fn(),
  updateCurrentUser: vi.fn(),
  getPreferenceChoices: vi.fn(),
  changePassword: vi.fn(),
  login: vi.fn(),
  logout: vi.fn(),
}))
vi.mock('@/api/notifications', () => ({
  registerDevice: vi.fn(),
  unregisterDevice: vi.fn(),
  getPushSettings: vi.fn(),
  updatePushSettings: vi.fn(),
}))
vi.mock('@/api/academics', () => ({
  getSchools: vi.fn(),
  getProgrammes: vi.fn(),
  getIntakes: vi.fn(),
}))

const completeStudent = makeStudent({
  profile_complete: true,
  student_profile: makeStudentProfile({
    student_number: 'AIU22001',
    school: 1,
    programme: 10,
    intake: 100,
    current_semester: 3,
    interests: ['cybersecurity'],
  }),
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
  vi.mocked(authApi.getPreferenceChoices).mockResolvedValue(preferenceChoices)
  vi.mocked(academicsApi.getSchools).mockResolvedValue(schools)
  vi.mocked(academicsApi.getIntakes).mockResolvedValue(intakes)
  vi.mocked(academicsApi.getProgrammes).mockImplementation(async (schoolId) =>
    programmes.filter((p) => p.school === schoolId),
  )
})

describe('Profile page', () => {
  it('links to the privacy notice', async () => {
    renderProfile()
    const link = await screen.findByRole('link', { name: 'Read the privacy notice' })
    expect(link.getAttribute('href')).toBe('/privacy')
  })

  it('shows the account and pre-fills the saved studies', async () => {
    renderProfile()

    expect(await screen.findByText('ali@student.aiu.edu.my')).toBeTruthy()
    expect(screen.getByText('Student')).toBeTruthy()
    const sections = screen.getByRole('navigation', { name: 'Profile sections' })
    expect([...sections.querySelectorAll('a')].map((link) => link.getAttribute('href'))).toEqual([
      '#account',
      '#studies',
      '#interests',
      '#appearance',
      '#password',
      '#privacy',
    ])
    expect(screen.getByRole('region', { name: 'Your studies' })).toBeTruthy()
    await waitFor(() => {
      expect((screen.getByLabelText('School') as HTMLSelectElement).value).toBe('1')
      expect((screen.getByLabelText('Programme') as HTMLSelectElement).value).toBe('10')
      expect((screen.getByLabelText('Intake') as HTMLSelectElement).value).toBe('100')
    })
    expect((screen.getByLabelText('Student number (optional)') as HTMLInputElement).value).toBe(
      'AIU22001',
    )
  })

  it('shows the worked-out semester and lets the student correct it', async () => {
    vi.mocked(authApi.updateCurrentUser).mockResolvedValue(completeStudent)
    renderProfile()

    expect(await screen.findByText('Semester 3', { selector: 'strong' })).toBeTruthy()
    await waitFor(() => {
      expect((screen.getByLabelText('Programme') as HTMLSelectElement).value).toBe('10')
    })
    fireEvent.change(screen.getByLabelText('Semester'), { target: { value: '4' } })
    fireEvent.click(screen.getByRole('button', { name: 'Save changes' }))

    await waitFor(() => {
      expect(authApi.updateCurrentUser).toHaveBeenCalledWith({
        student_profile: {
          school: 1,
          programme: 10,
          intake: 100,
          student_number: 'AIU22001',
          semester_override: 4,
        },
      })
    })
  })

  it('pre-fills and saves interests', async () => {
    vi.mocked(authApi.updateCurrentUser).mockResolvedValue(completeStudent)
    renderProfile()

    const cyber = (await screen.findByLabelText('Cybersecurity')) as HTMLInputElement
    expect(cyber.checked).toBe(true)
    fireEvent.click(screen.getByLabelText('Bootcamps'))
    fireEvent.click(screen.getByRole('button', { name: 'Save interests' }))

    expect(await screen.findByText('Saved.')).toBeTruthy()
    expect(authApi.updateCurrentUser).toHaveBeenCalledWith({
      student_profile: { interests: ['cybersecurity'], info_types: ['bootcamp'], aliases: '' },
    })
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

describe('Phone notifications', () => {
  const allOn = { class_changes: true, needs_you: true, daily_digest: true }

  beforeEach(() => {
    vi.mocked(notificationsApi.getPushSettings).mockResolvedValue(allOn)
    vi.mocked(notificationsApi.registerDevice).mockResolvedValue()
  })

  afterEach(() => {
    delete window.UniFlowApp
  })

  it('are shown only inside the phone app', async () => {
    renderProfile()

    expect(await screen.findByText('ali@student.aiu.edu.my')).toBeTruthy()
    expect(screen.queryByRole('region', { name: 'Phone notifications' })).toBeNull()
    expect(notificationsApi.getPushSettings).not.toHaveBeenCalled()
  })

  it('switch an alert off for this phone', async () => {
    window.UniFlowApp = { bridgeVersion: 1, platform: 'android', appVersion: '1.0.0', pushToken: null }
    vi.mocked(notificationsApi.updatePushSettings).mockResolvedValue({ ...allOn, daily_digest: false })
    renderProfile()

    const digest = await screen.findByRole('switch', { name: /Daily digest/ })
    expect(screen.getByRole('switch', { name: /Class changes/ }).getAttribute('aria-checked')).toBe('true')
    fireEvent.click(digest)

    await waitFor(() => expect(notificationsApi.updatePushSettings).toHaveBeenCalledWith({ daily_digest: false }))
    await waitFor(() => expect(digest.getAttribute('aria-checked')).toBe('false'))
  })
})
