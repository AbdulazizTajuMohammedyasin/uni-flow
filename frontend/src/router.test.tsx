import { QueryClientProvider } from '@tanstack/react-query'
import { render, screen, within } from '@testing-library/react'
import { createMemoryRouter, RouterProvider } from 'react-router'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import * as authApi from '@/api/auth'
import { AuthProvider } from '@/context/AuthContext'
import type { User } from '@/types/auth'

import { createQueryClient } from './lib/queryClient'
import { RouteErrorPage } from './pages/RouteError/RouteError'
import { createAppRoutes } from './router'

// The layout shows the dev-only API health badge; answer it with a fake "ok" (no network).
vi.mock('@/api/health', () => ({
  getHealth: vi.fn().mockResolvedValue({ status: 'ok', db: 'ok' }),
}))

// Pretend the session is restored as a logged-in student (no network).
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
  profile_complete: true,
  student_profile: { student_number: null, school: 1, programme: 1, intake: 1 },
  staff_profile: null,
}

beforeEach(() => {
  vi.mocked(authApi.restoreSession).mockResolvedValue(true)
  vi.mocked(authApi.getCurrentUser).mockResolvedValue(student)
})

/** Render the real route tree at a given address, without a real browser URL bar. */
function renderAt(path: string) {
  const router = createMemoryRouter(createAppRoutes(), { initialEntries: [path] })
  render(
    <QueryClientProvider client={createQueryClient()}>
      <AuthProvider>
        <RouterProvider router={router} />
      </AuthProvider>
    </QueryClientProvider>,
  )
  return router
}

describe('student area (AppLayout)', () => {
  it('renders the home page with sidebar and bottom navigation', async () => {
    renderAt('/')

    expect(await screen.findByRole('heading', { level: 1, name: 'Home' })).toBeTruthy()

    const sidebar = screen.getByRole('navigation', { name: 'Sidebar' })
    for (const label of ['Home', 'Announcements', 'Events', 'Timetable', 'Communities']) {
      expect(within(sidebar).getByRole('link', { name: label })).toBeTruthy()
    }

    const bottom = screen.getByRole('navigation', { name: 'Bottom navigation' })
    expect(within(bottom).getAllByRole('link')).toHaveLength(5)
  })

  it('highlights the active link', async () => {
    renderAt('/events')

    await screen.findByRole('heading', { level: 1, name: 'Events' })
    const sidebar = screen.getByRole('navigation', { name: 'Sidebar' })

    expect(within(sidebar).getByRole('link', { name: 'Events' }).getAttribute('aria-current')).toBe(
      'page',
    )
    expect(within(sidebar).getByRole('link', { name: 'Home' }).getAttribute('aria-current')).toBeNull()
  })
})

describe('login protection', () => {
  it('sends visitors who are not logged in to /login, remembering where they were going', async () => {
    vi.mocked(authApi.restoreSession).mockResolvedValue(false)

    const router = renderAt('/events')

    expect(await screen.findByRole('heading', { level: 1, name: 'Log in' })).toBeTruthy()
    expect(router.state.location.pathname).toBe('/login')
    expect(router.state.location.search).toBe('?next=%2Fevents')
  })
})

describe('other areas', () => {
  it('shows the login and register pages to visitors, without the student navigation', async () => {
    vi.mocked(authApi.restoreSession).mockResolvedValue(false)

    renderAt('/login')
    expect(await screen.findByRole('heading', { level: 1, name: 'Log in' })).toBeTruthy()
    expect(screen.queryByRole('navigation', { name: 'Sidebar' })).toBeNull()
  })

  it('sends a logged-in user away from /login to Home', async () => {
    const router = renderAt('/login')

    expect(await screen.findByRole('heading', { level: 1, name: 'Home' })).toBeTruthy()
    expect(router.state.location.pathname).toBe('/')
  })

  it('renders the staff dashboard in the staff layout', async () => {
    renderAt('/staff')

    expect(await screen.findByRole('heading', { level: 1, name: 'Staff dashboard' })).toBeTruthy()
    expect(screen.getByRole('link', { name: '← Back to UniFlow' })).toBeTruthy()
  })

  it('shows the 404 page for unknown addresses', async () => {
    renderAt('/this-page-does-not-exist')

    expect(await screen.findByRole('heading', { name: 'Page not found' })).toBeTruthy()
    expect(screen.getByRole('link', { name: 'Go to home' }).getAttribute('href')).toBe('/')
  })
})

describe('RouteErrorPage', () => {
  it('shows a friendly error instead of a blank screen when a page crashes', async () => {
    // React logs the thrown error to the console; silence it for this test.
    const consoleError = vi.spyOn(console, 'error').mockImplementation(() => {})
    function Broken(): never {
      throw new Error('boom')
    }
    const router = createMemoryRouter([
      { path: '/', element: <Broken />, errorElement: <RouteErrorPage /> },
    ])

    render(<RouterProvider router={router} />)

    expect(await screen.findByRole('alert')).toBeTruthy()
    expect(screen.getByText('Something went wrong')).toBeTruthy()
    expect(screen.getByRole('button', { name: 'Reload page' })).toBeTruthy()
    consoleError.mockRestore()
  })
})
