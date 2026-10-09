import { QueryClientProvider } from '@tanstack/react-query'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { createMemoryRouter, RouterProvider } from 'react-router'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import * as feedApi from '@/api/feed'
import { createQueryClient } from '@/lib/queryClient'
import type { FeedItem } from '@/types/feed'

import { SearchPage } from './Search'

vi.mock('@/api/feed', () => ({ searchFeed: vi.fn() }))

const petronas: FeedItem = {
  id: 9,
  kind: 'internship',
  info_type: 'internship',
  tier: 'digest',
  title: 'Petronas internship',
  summary: 'Apply by 20 Oct.',
  importance: 60,
  relevance: 65,
  reason: 'For Computer Science students',
  action_required: false,
  action_text: '',
  starts_at: null,
  deadline_at: null,
  location: '',
  link: '',
  not_confirmed: false,
  official: false,
  read: true,
  published_at: '2026-10-05T01:00:00Z',
}

function renderPage(path = '/search') {
  const router = createMemoryRouter([{ path: '/search', element: <SearchPage /> }], {
    initialEntries: [path],
  })
  render(
    <QueryClientProvider client={createQueryClient()}>
      <RouterProvider router={router} />
    </QueryClientProvider>,
  )
  return router
}

beforeEach(() => {
  vi.mocked(feedApi.searchFeed).mockResolvedValue([petronas])
})

describe('Search page', () => {
  it('searches my items and shows them as cards', async () => {
    const router = renderPage()
    fireEvent.change(screen.getByLabelText('Search your items'), { target: { value: ' petronas ' } })
    fireEvent.click(screen.getByRole('button', { name: 'Search' }))

    expect(await screen.findByText('Petronas internship')).toBeTruthy()
    expect(feedApi.searchFeed).toHaveBeenCalledWith('petronas')
    expect(router.state.location.search).toBe('?q=petronas')
    expect(screen.getByRole('link', { name: /Petronas internship/ }).getAttribute('href')).toBe('/insights/9')
  })

  it('opens with the words from the address, and says when nothing matches', async () => {
    vi.mocked(feedApi.searchFeed).mockResolvedValue([])
    renderPage('/search?q=scholarship')

    expect(await screen.findByText('Nothing found')).toBeTruthy()
    expect((screen.getByLabelText('Search your items') as HTMLInputElement).value).toBe('scholarship')
  })

  it('does not search for fewer than 2 characters', async () => {
    renderPage('/search?q=a')
    fireEvent.change(screen.getByLabelText('Search your items'), { target: { value: 'a' } })
    expect((screen.getByRole('button', { name: 'Search' }) as HTMLButtonElement).disabled).toBe(true)
    await waitFor(() => expect(feedApi.searchFeed).not.toHaveBeenCalled())
  })
})
