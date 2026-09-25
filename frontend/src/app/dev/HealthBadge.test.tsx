import { QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { ApiError } from '@/shared/api/errors'
import { getHealth } from '@/shared/api/health'

import { createQueryClient } from '../queryClient'
import { HealthBadge } from './HealthBadge'

// Replace the real network call with a controllable fake.
vi.mock('@/shared/api/health', () => ({ getHealth: vi.fn() }))
const mockedGetHealth = vi.mocked(getHealth)

function renderBadge() {
  render(
    <QueryClientProvider client={createQueryClient()}>
      <HealthBadge />
    </QueryClientProvider>,
  )
}

beforeEach(() => {
  mockedGetHealth.mockReset()
})

describe('HealthBadge', () => {
  it('shows "checking" while the request is in flight', () => {
    mockedGetHealth.mockReturnValue(new Promise(() => {})) // never resolves
    renderBadge()
    expect(screen.getByText('API: checking…')).toBeTruthy()
  })

  it('shows "ok" when the API and database are healthy', async () => {
    mockedGetHealth.mockResolvedValue({ status: 'ok', db: 'ok' })
    renderBadge()
    expect(await screen.findByText('API: ok')).toBeTruthy()
  })

  it('shows "offline" when the API cannot be reached', async () => {
    mockedGetHealth.mockRejectedValue(
      new ApiError({ status: null, code: 'network_error', message: 'Cannot reach the server.' }),
    )
    renderBadge()
    expect(await screen.findByText('API: offline')).toBeTruthy()
  })
})
