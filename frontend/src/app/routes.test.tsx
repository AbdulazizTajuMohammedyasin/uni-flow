import { render, screen, within } from '@testing-library/react'
import { createMemoryRouter, RouterProvider } from 'react-router'
import { describe, expect, it, vi } from 'vitest'

import { RouteErrorPage } from './pages/RouteErrorPage'
import { createAppRoutes } from './routes'

/** Render the real route tree at a given address, without a real browser URL bar. */
function renderAt(path: string) {
  const router = createMemoryRouter(createAppRoutes(), { initialEntries: [path] })
  render(<RouterProvider router={router} />)
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

describe('other areas', () => {
  it('renders the login page in the auth layout, without the student navigation', async () => {
    renderAt('/login')

    expect(await screen.findByRole('heading', { level: 1, name: 'Log in' })).toBeTruthy()
    expect(screen.queryByRole('navigation', { name: 'Sidebar' })).toBeNull()
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
