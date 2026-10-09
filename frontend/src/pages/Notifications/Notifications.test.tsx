import { QueryClientProvider } from '@tanstack/react-query'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { createMemoryRouter, RouterProvider } from 'react-router'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import * as notificationsApi from '@/api/notifications'
import { createQueryClient } from '@/lib/queryClient'
import { notificationLink, timeAgo } from '@/lib/notifications'
import type { AppNotification } from '@/types/notifications'

import { NotificationsPage } from './Notifications'

vi.mock('@/api/notifications', () => ({
  getNotifications: vi.fn(),
  getUnreadCount: vi.fn(),
  markNotificationRead: vi.fn(),
  markAllNotificationsRead: vi.fn(),
}))

function alert(overrides: Partial<AppNotification>): AppNotification {
  return {
    id: 1,
    kind: 'direct_attention',
    title: 'See Dr Lee about your FYP',
    body: 'Dr Lee asks Ali to see him.',
    target_type: 'insight',
    target_id: 42,
    read: false,
    created_at: new Date(Date.now() - 5 * 60_000).toISOString(),
    ...overrides,
  }
}

function renderPage() {
  const router = createMemoryRouter(
    [
      { path: '/notifications', element: <NotificationsPage /> },
      { path: '/insights/:id', element: <h1>Item page</h1> },
      { path: '/digest', element: <h1>Digest page</h1> },
    ],
    { initialEntries: ['/notifications'] },
  )
  render(
    <QueryClientProvider client={createQueryClient()}>
      <RouterProvider router={router} />
    </QueryClientProvider>,
  )
  return router
}

beforeEach(() => {
  vi.mocked(notificationsApi.getNotifications).mockResolvedValue([
    alert({ id: 1 }),
    alert({
      id: 2,
      kind: 'digest',
      title: 'Your daily digest: 4 new items',
      body: 'Hackathon · Club fair',
      target_type: 'digest',
      target_id: 20261009,
      read: true,
    }),
  ])
  vi.mocked(notificationsApi.markNotificationRead).mockResolvedValue()
  vi.mocked(notificationsApi.markAllNotificationsRead).mockResolvedValue()
})

describe('Notifications page', () => {
  it('lists my alerts with their kind and time', async () => {
    renderPage()
    expect(await screen.findByText('See Dr Lee about your FYP')).toBeTruthy()
    expect(screen.getByText('You were named · 5 min ago')).toBeTruthy()
    expect(screen.getByText('Your daily digest: 4 new items')).toBeTruthy()
  })

  it('opening an unread alert marks it read and opens its item', async () => {
    const router = renderPage()
    fireEvent.click(await screen.findByRole('button', { name: /See Dr Lee/ }))

    await waitFor(() => expect(notificationsApi.markNotificationRead).toHaveBeenCalledWith(1))
    expect(router.state.location.pathname).toBe('/insights/42')
  })

  it("the digest alert opens that day's digest", async () => {
    const router = renderPage()
    fireEvent.click(await screen.findByRole('button', { name: /daily digest/ }))

    await waitFor(() => expect(router.state.location.search).toBe('?date=2026-10-09'))
    expect(notificationsApi.markNotificationRead).not.toHaveBeenCalled() // already read
  })

  it('marks all as read', async () => {
    renderPage()
    fireEvent.click(await screen.findByRole('button', { name: 'Mark all as read' }))
    await waitFor(() => expect(notificationsApi.markAllNotificationsRead).toHaveBeenCalled())
  })

  it('explains when there are none', async () => {
    vi.mocked(notificationsApi.getNotifications).mockResolvedValue([])
    renderPage()
    expect(await screen.findByText('No notifications yet')).toBeTruthy()
    expect(screen.queryByRole('button', { name: 'Mark all as read' })).toBeNull()
  })
})

describe('notification helpers', () => {
  it('knows where each alert goes', () => {
    expect(notificationLink(alert({}))).toBe('/insights/42')
    expect(notificationLink(alert({ target_type: 'digest', target_id: 20261009 }))).toBe('/digest?date=2026-10-09')
    expect(notificationLink(alert({ target_type: '', target_id: null }))).toBeNull()
  })

  it('says how long ago', () => {
    const now = Date.parse('2026-10-09T12:00:00Z')
    expect(timeAgo('2026-10-09T11:59:40Z', now)).toBe('just now')
    expect(timeAgo('2026-10-09T09:00:00Z', now)).toBe('3 h ago')
    expect(timeAgo('2026-10-01T09:00:00Z', now)).toBe('1 Oct')
  })
})
