import { QueryClientProvider } from '@tanstack/react-query'
import { render, screen, within } from '@testing-library/react'
import { createMemoryRouter, RouterProvider } from 'react-router'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import * as feedApi from '@/api/feed'
import { createQueryClient } from '@/lib/queryClient'
import type { FeedItem } from '@/types/feed'

import { ForYouPage } from './ForYou'

vi.mock('@/api/feed', () => ({ getFeed: vi.fn(), getFeedItem: vi.fn(), updateFeedItem: vi.fn() }))

function feedItem(overrides: Partial<FeedItem> = {}): FeedItem {
  return {
    id: 1,
    kind: 'academic_notice',
    info_type: 'academic_notice',
    tier: 'digest',
    title: 'Library hours',
    summary: 'The library opens at 8.',
    importance: 30,
    relevance: 60,
    reason: 'For School of Computing students',
    action_required: false,
    action_text: '',
    starts_at: null,
    deadline_at: null,
    location: '',
    link: '',
    not_confirmed: false,
    official: false,
    read: false,
    published_at: '2026-10-05T01:00:00Z',
    ...overrides,
  }
}

function renderPage() {
  const router = createMemoryRouter([{ path: '/', element: <ForYouPage /> }])
  render(
    <QueryClientProvider client={createQueryClient()}>
      <RouterProvider router={router} />
    </QueryClientProvider>,
  )
}

beforeEach(() => {
  vi.mocked(feedApi.getFeed).mockResolvedValue([
    feedItem({ id: 1, tier: 'direct', title: 'See Dr Lee', reason: 'You were named in this message' }),
    feedItem({
      id: 2,
      tier: 'action',
      title: 'Apply for Petronas',
      deadline_at: '2026-10-20T08:00:00Z',
      reason: 'For Computer Science students',
    }),
    feedItem({ id: 3, tier: 'digest', title: 'Maybe a quiz?', not_confirmed: true, read: true }),
  ])
})

describe('For you page', () => {
  it('shows my items in the four levels, in order, hiding empty ones', async () => {
    renderPage()

    expect(await screen.findByText('See Dr Lee')).toBeTruthy()
    const sections = screen.getAllByRole('region').map((section) => section.getAttribute('aria-label'))
    expect(sections).toEqual(['Direct attention', 'Action required', 'Digest'])

    const action = screen.getByRole('region', { name: 'Action required' })
    expect(within(action).getByText('Due Tue 20 Oct, 16:00 · For Computer Science students')).toBeTruthy()
    expect(within(action).getByRole('link').getAttribute('href')).toBe('/insights/2')

    const digest = screen.getByRole('region', { name: 'Digest' })
    expect(within(digest).getByText('Not confirmed')).toBeTruthy()
    expect(screen.getAllByLabelText('Unread')).toHaveLength(2)
  })

  it('explains what to do when nothing is there yet', async () => {
    vi.mocked(feedApi.getFeed).mockResolvedValue([])
    renderPage()
    expect(await screen.findByText('Nothing for you yet')).toBeTruthy()
  })
})
