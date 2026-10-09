import { QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor, within } from '@testing-library/react'
import { createMemoryRouter, RouterProvider } from 'react-router'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import * as feedApi from '@/api/feed'
import { createQueryClient } from '@/lib/queryClient'
import type { FeedItem } from '@/types/feed'

import { DigestPage } from './Digest'

vi.mock('@/api/feed', () => ({
  getFeed: vi.fn(),
  getDigest: vi.fn(),
  getFeedItem: vi.fn(),
  updateFeedItem: vi.fn(),
}))

function item(id: number, title: string, info_type: string, extra: Partial<FeedItem> = {}): FeedItem {
  return {
    id,
    kind: info_type || 'deadline',
    info_type,
    tier: 'digest',
    title,
    summary: 'Summary.',
    importance: 30,
    relevance: 50,
    reason: 'Because',
    action_required: false,
    action_text: '',
    starts_at: null,
    deadline_at: null,
    location: '',
    link: '',
    not_confirmed: false,
    official: false,
    read: false,
    published_at: '2026-10-09T01:00:00Z',
    ...extra,
  }
}

function renderPage(path = '/digest?date=2026-10-09') {
  const router = createMemoryRouter([{ path: '/digest', element: <DigestPage /> }], {
    initialEntries: [path],
  })
  render(
    <QueryClientProvider client={createQueryClient()}>
      <RouterProvider router={router} />
    </QueryClientProvider>,
  )
}

beforeEach(() => {
  vi.mocked(feedApi.getDigest).mockResolvedValue({
    date: '2026-10-09',
    items: [
      item(1, 'Internship fair', 'internship'),
      item(2, 'Library open late', 'student_affairs'),
      item(3, 'Maybe a quiz?', 'academic_notice', { not_confirmed: true }),
      item(4, 'Club fair', 'student_affairs'),
    ],
  })
})

describe('Digest page', () => {
  it("shows that day's items grouped by type", async () => {
    renderPage()

    expect(await screen.findByText('Good to know, Friday 9 Oct.')).toBeTruthy()
    expect(feedApi.getDigest).toHaveBeenCalledWith('2026-10-09')
    const groups = screen.getAllByRole('region').map((group) => group.getAttribute('aria-label'))
    expect(groups).toEqual(['Academic notices', 'Student affairs', 'Internships'])

    const affairs = screen.getByRole('region', { name: 'Student affairs' })
    expect(within(affairs).getAllByRole('link').map((link) => link.textContent)).toEqual([
      'Library open lateSummary.',
      'Club fairSummary.',
    ])
    expect(screen.getByText('Not confirmed')).toBeTruthy()
    expect(screen.getByRole('link', { name: /Internship fair/ }).getAttribute('href')).toBe('/insights/1')
  })

  it('shows my latest digest without a date, and says when there is none yet', async () => {
    vi.mocked(feedApi.getDigest).mockResolvedValue({ date: null, items: [] })
    renderPage('/digest')

    await waitFor(() => expect(feedApi.getDigest).toHaveBeenCalledWith(undefined))
    expect(await screen.findByText('Your first digest arrives one evening at 7 pm.')).toBeTruthy()
    expect(screen.getByText('Nothing in this digest')).toBeTruthy()
  })
})
