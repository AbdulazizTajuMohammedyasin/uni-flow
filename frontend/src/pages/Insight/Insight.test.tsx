import { QueryClientProvider } from '@tanstack/react-query'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { createMemoryRouter, RouterProvider } from 'react-router'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { ApiError } from '@/api/errors'
import * as feedApi from '@/api/feed'
import { createQueryClient } from '@/lib/queryClient'
import type { FeedDetail } from '@/types/feed'

import { InsightPage } from './Insight'

vi.mock('@/api/feed', () => ({ getFeed: vi.fn(), getFeedItem: vi.fn(), updateFeedItem: vi.fn() }))

const detail: FeedDetail = {
  id: 7,
  kind: 'internship',
  tier: 'action',
  title: 'Petronas internship',
  summary: 'Petronas is taking 3rd-year interns.',
  importance: 80,
  relevance: 65,
  reason: 'For Computer Science students',
  action_required: true,
  action_text: 'Apply online',
  starts_at: null,
  deadline_at: '2026-10-20T08:00:00Z',
  location: '',
  link: 'https://careers.example.com/apply',
  not_confirmed: false,
  official: false,
  read: false,
  published_at: '2026-10-05T01:00:00Z',
  data: {},
  topics: [],
  evidence: [
    {
      group: { id: 3, platform: 'telegram_channel', title: 'AIU Careers' },
      sender_name: 'Career Office',
      sent_at: '2026-10-05T01:00:00Z',
      quote: 'Petronas internship for BCS Year 3, apply by 20 Oct.',
      open_url: 'https://t.me/aiucareers/42',
    },
  ],
  timetable_change: null,
  dismissed: false,
}

function renderPage() {
  const router = createMemoryRouter(
    [
      { path: '/insights/:insightId', element: <InsightPage /> },
      { path: '/', element: <h1>For you</h1> },
    ],
    { initialEntries: ['/insights/7'] },
  )
  render(
    <QueryClientProvider client={createQueryClient()}>
      <RouterProvider router={router} />
    </QueryClientProvider>,
  )
  return router
}

beforeEach(() => {
  vi.mocked(feedApi.getFeedItem).mockResolvedValue(detail)
  vi.mocked(feedApi.updateFeedItem).mockResolvedValue()
})

describe('Insight page', () => {
  it('shows the details, why I see it, and the original message', async () => {
    renderPage()

    expect(await screen.findByRole('heading', { level: 1, name: 'Petronas internship' })).toBeTruthy()
    expect(screen.getByText('Why you see this: For Computer Science students')).toBeTruthy()
    expect(screen.getByRole('note').textContent).toBe('What to do: Apply online')
    expect(screen.getByText('Tue 20 Oct, 16:00')).toBeTruthy()
    expect(screen.getByText('“Petronas internship for BCS Year 3, apply by 20 Oct.”')).toBeTruthy()
    expect(screen.getByRole('link', { name: 'Open original' }).getAttribute('href')).toBe(
      'https://t.me/aiucareers/42',
    )
  })

  it('is marked as read when opened', async () => {
    renderPage()
    await waitFor(() => expect(feedApi.updateFeedItem).toHaveBeenCalledWith(7, 'read'))
  })

  it('can be marked "not relevant", then goes back to For you', async () => {
    const router = renderPage()
    fireEvent.click(await screen.findByRole('button', { name: 'Not relevant to me' }))

    await waitFor(() => expect(feedApi.updateFeedItem).toHaveBeenCalledWith(7, 'not_relevant'))
    await waitFor(() => expect(router.state.location.pathname).toBe('/'))
  })

  it('links a timetable change to the timetable page', async () => {
    vi.mocked(feedApi.getFeedItem).mockResolvedValue({
      ...detail,
      kind: 'class_moved',
      action_required: false,
      timetable_change: { id: 4, my_status: 'pending' },
    })
    renderPage()
    expect(await screen.findByRole('link', { name: 'Confirm or reject it on your timetable' })).toBeTruthy()
  })

  it('says so when the item is not mine', async () => {
    vi.mocked(feedApi.getFeedItem).mockRejectedValue(
      new ApiError({ status: 404, code: 'not_found', message: 'Not found.', fields: {} }),
    )
    renderPage()
    expect(await screen.findByText('This item is not in your feed')).toBeTruthy()
  })
})
