import { QueryClientProvider } from '@tanstack/react-query'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import * as sourcesApi from '@/api/sources'
import { ApiError } from '@/api/errors'
import { createQueryClient } from '@/lib/queryClient'
import type { Source } from '@/types/sources'

import { SourcesPage } from './Sources'

vi.mock('@/api/sources', () => ({
  getMySources: vi.fn(),
  createSource: vi.fn(),
  pasteMessages: vi.fn(),
  uploadExport: vi.fn(),
}))

const group: Source = {
  id: 7,
  title: 'CDE2313 Sec A',
  platform: 'manual',
  platform_label: 'Pasted or uploaded',
  status: 'active',
  school: null,
  programme: null,
  intake: null,
  course: null,
  section: null,
  message_count: 12,
}

function renderPage() {
  render(
    <QueryClientProvider client={createQueryClient()}>
      <SourcesPage />
    </QueryClientProvider>,
  )
}

beforeEach(() => {
  vi.mocked(sourcesApi.getMySources).mockResolvedValue([group])
})

describe('Groups page', () => {
  it('lists my groups with their message counts', async () => {
    renderPage()
    expect(await screen.findByText('CDE2313 Sec A')).toBeTruthy()
    expect(screen.getByText('Pasted or uploaded · 12 messages')).toBeTruthy()
  })

  it('explains what to do when there are no groups', async () => {
    vi.mocked(sourcesApi.getMySources).mockResolvedValue([])
    renderPage()
    expect(await screen.findByText('No groups yet')).toBeTruthy()
  })

  it('adds a group', async () => {
    vi.mocked(sourcesApi.createSource).mockResolvedValue({ ...group, id: 8, title: 'SCI notices' })
    renderPage()

    fireEvent.change(await screen.findByLabelText('Group name'), { target: { value: ' SCI notices ' } })
    fireEvent.click(screen.getByRole('button', { name: 'Add group' }))

    await waitFor(() => expect(sourcesApi.createSource).toHaveBeenCalledWith('SCI notices'))
    await waitFor(() => expect((screen.getByLabelText('Group name') as HTMLInputElement).value).toBe(''))
  })

  it('pastes messages and says how many were new', async () => {
    vi.mocked(sourcesApi.pasteMessages).mockResolvedValue({ added: 2, already_stored: 1 })
    renderPage()

    fireEvent.click(await screen.findByRole('button', { name: 'Paste messages' }))
    fireEvent.change(screen.getByLabelText('Messages'), {
      target: { value: '[09:12, 01/10/2026] Dr Lee: Class moved to 2 PM.' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Add messages' }))

    expect(await screen.findByText('2 new messages added (1 UniFlow already had).')).toBeTruthy()
    expect(sourcesApi.pasteMessages).toHaveBeenCalledWith(7, '[09:12, 01/10/2026] Dr Lee: Class moved to 2 PM.')
  })

  it('uploads a WhatsApp export', async () => {
    vi.mocked(sourcesApi.uploadExport).mockResolvedValue({ added: 1, already_stored: 0 })
    renderPage()

    fireEvent.click(await screen.findByRole('button', { name: 'Upload WhatsApp export' }))
    const file = new File(['01/10/2026, 09:12 - Dr Lee: hi'], 'chat.txt', { type: 'text/plain' })
    fireEvent.change(screen.getByLabelText('WhatsApp export (.txt)'), { target: { files: [file] } })
    fireEvent.click(screen.getByRole('button', { name: 'Upload' }))

    expect(await screen.findByText('1 new message added.')).toBeTruthy()
    expect(sourcesApi.uploadExport).toHaveBeenCalledWith(7, file)
  })

  it("shows the backend's explanation when an upload is refused", async () => {
    vi.mocked(sourcesApi.uploadExport).mockRejectedValue(
      new ApiError({
        status: 400,
        code: 'validation_error',
        message: 'Invalid input.',
        fields: { file: ['Upload the .txt file from WhatsApp\'s "Export chat".'] },
      }),
    )
    renderPage()

    fireEvent.click(await screen.findByRole('button', { name: 'Upload WhatsApp export' }))
    const file = new File(['%PDF'], 'chat.pdf')
    fireEvent.change(screen.getByLabelText('WhatsApp export (.txt)'), { target: { files: [file] } })
    fireEvent.click(screen.getByRole('button', { name: 'Upload' }))

    expect(await screen.findByText('Upload the .txt file from WhatsApp\'s "Export chat".')).toBeTruthy()
  })
})
