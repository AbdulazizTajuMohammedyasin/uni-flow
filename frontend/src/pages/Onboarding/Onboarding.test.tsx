import { QueryClientProvider } from '@tanstack/react-query'
import { fireEvent, render, screen, within } from '@testing-library/react'
import { createMemoryRouter, RouterProvider } from 'react-router'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import * as academicsApi from '@/api/academics'
import * as authApi from '@/api/auth'
import { AuthProvider } from '@/context/AuthContext'
import { createQueryClient } from '@/lib/queryClient'
import { intakes, makeStudent, preferenceChoices, programmes, schools } from '@/test/fixtures'

import { OnboardingPage } from './Onboarding'

vi.mock('@/api/auth', () => ({
  restoreSession: vi.fn(),
  getCurrentUser: vi.fn(),
  updateCurrentUser: vi.fn(),
  getPreferenceChoices: vi.fn(),
  login: vi.fn(),
  logout: vi.fn(),
}))
vi.mock('@/api/academics', () => ({
  getSchools: vi.fn(),
  getProgrammes: vi.fn(),
  getIntakes: vi.fn(),
}))

function renderOnboarding() {
  const router = createMemoryRouter(
    [
      { path: '/onboarding', element: <OnboardingPage /> },
      { path: '/', element: <h1>Home</h1> },
    ],
    { initialEntries: ['/onboarding'] },
  )
  render(
    <QueryClientProvider client={createQueryClient()}>
      <AuthProvider>
        <RouterProvider router={router} />
      </AuthProvider>
    </QueryClientProvider>,
  )
}

function select(label: string, value: string | number) {
  fireEvent.change(screen.getByLabelText(label), { target: { value: String(value) } })
}

beforeEach(() => {
  vi.mocked(authApi.restoreSession).mockResolvedValue(true)
  vi.mocked(authApi.getCurrentUser).mockResolvedValue(makeStudent())
  vi.mocked(authApi.getPreferenceChoices).mockResolvedValue(preferenceChoices)
  vi.mocked(academicsApi.getSchools).mockResolvedValue(schools)
  vi.mocked(academicsApi.getIntakes).mockResolvedValue(intakes)
  vi.mocked(academicsApi.getProgrammes).mockImplementation(async (schoolId) =>
    programmes.filter((p) => p.school === schoolId),
  )
})

describe('Onboarding page', () => {
  it("lists only the chosen school's programmes, and resets the programme when the school changes", async () => {
    renderOnboarding()
    await screen.findByRole('option', { name: 'School of Computing and Informatics' })
    expect((screen.getByLabelText('Programme') as HTMLSelectElement).disabled).toBe(true)

    select('School', 1)
    // The programme dropdown is redrawn when its options load, so look it up again.
    await screen.findByRole('option', { name: 'Bachelor in Computer Science (Honours)' })
    const programme = screen.getByLabelText('Programme')
    expect(within(programme).queryByRole('option', { name: /Business Administration/ })).toBeNull()

    select('Programme', 10)
    select('School', 2)
    await screen.findByRole('option', { name: 'Bachelor of Business Administration (Honours)' })
    expect((screen.getByLabelText('Programme') as HTMLSelectElement).value).toBe('')
  })

  it('asks for all three choices', async () => {
    renderOnboarding()
    fireEvent.click(await screen.findByRole('button', { name: 'Continue' }))

    expect(await screen.findByText('Choose your school.')).toBeTruthy()
    expect(screen.getByText('Choose your programme.')).toBeTruthy()
    expect(screen.getByText('Choose your intake.')).toBeTruthy()
    expect(authApi.updateCurrentUser).not.toHaveBeenCalled()
  })

  async function saveStudies() {
    vi.mocked(authApi.updateCurrentUser).mockResolvedValue(makeStudent({ profile_complete: true }))
    renderOnboarding()
    await screen.findByRole('option', { name: 'School of Computing and Informatics' })

    select('School', 1)
    await screen.findByRole('option', { name: 'Bachelor in Computer Science (Honours)' })
    select('Programme', 10)
    select('Intake', 100)
    fireEvent.click(screen.getByRole('button', { name: 'Continue' }))
    await screen.findByRole('heading', { name: 'What matters to you?' })
  }

  it('saves the studies, then asks for interests (which can be skipped)', async () => {
    await saveStudies()
    expect(authApi.updateCurrentUser).toHaveBeenCalledWith({
      student_profile: { school: 1, programme: 10, intake: 100, student_number: null },
    })

    fireEvent.click(screen.getByRole('button', { name: 'Skip for now' }))
    expect(await screen.findByRole('heading', { name: 'Home' })).toBeTruthy()
  })

  it('saves the chosen interests and information types, then goes Home', async () => {
    await saveStudies()

    fireEvent.click(await screen.findByLabelText('Artificial Intelligence'))
    fireEvent.click(screen.getByLabelText('Internships'))
    fireEvent.change(screen.getByLabelText('Nicknames (optional)'), { target: { value: 'Ali' } })
    fireEvent.click(screen.getByRole('button', { name: 'Finish' }))

    expect(await screen.findByRole('heading', { name: 'Home' })).toBeTruthy()
    expect(authApi.updateCurrentUser).toHaveBeenLastCalledWith({
      student_profile: { interests: ['ai'], info_types: ['internship'], aliases: 'Ali' },
    })
  })
})
