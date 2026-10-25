import { QueryClientProvider } from '@tanstack/react-query'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import * as sourcesApi from '@/api/sources'
import { ApiError } from '@/api/errors'
import { createQueryClient } from '@/lib/queryClient'
import type { Source } from '@/types/sources'

import { SourcesPage } from './Sources'

vi.mock('@/api/sources', () => ({
  getMySources: vi.fn(),
  createSource: vi.fn(),
  connectSource: vi.fn(),
  getUnclaimedGroups: vi.fn(),
  claimGroup: vi.fn(),
  leaveSource: vi.fn(),
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
  added_by_number: false,
  uniflow_number: '',
}

/** Radix menus open from the keyboard (jsdom has no pointer events). */
async function chooseFromMenu(item: string) {
  fireEvent.keyDown(await screen.findByRole('button', { name: 'Add messages to CDE2313 Sec A' }), { key: 'Enter' })
  fireEvent.click(await screen.findByRole('menuitem', { name: item }))
}

function renderPage() {
  render(
    <QueryClientProvider client={createQueryClient()}>
      <MemoryRouter>
        <SourcesPage />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

beforeEach(() => {
  vi.mocked(sourcesApi.getMySources).mockResolvedValue([group])
  vi.mocked(sourcesApi.getUnclaimedGroups).mockResolvedValue([])
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
    fireEvent.click(screen.getByRole('radio', { name: "I'll paste messages" }))
    fireEvent.click(screen.getByRole('button', { name: 'Add group' }))

    await waitFor(() => expect(sourcesApi.createSource).toHaveBeenCalledWith('SCI notices'))
    await waitFor(() => expect((screen.getByLabelText('Group name') as HTMLInputElement).value).toBe(''))
  })

  it('adds a WhatsApp group by its invite link', async () => {
    vi.mocked(sourcesApi.connectSource).mockResolvedValue({
      ...group,
      id: 9,
      title: 'CDE2313 Section A',
      platform: 'whatsapp_group',
      platform_label: 'WhatsApp group',
      status: 'pending',
      message_count: 0,
    })
    renderPage()

    fireEvent.change(await screen.findByLabelText('Group name'), { target: { value: 'CDE2313 Section A' } })
    fireEvent.change(screen.getByLabelText('WhatsApp invite link'), {
      target: { value: ' https://chat.whatsapp.com/AbCdEf123456 ' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Add group' }))

    await waitFor(() =>
      expect(sourcesApi.connectSource).toHaveBeenCalledWith('https://chat.whatsapp.com/AbCdEf123456', 'CDE2313 Section A'),
    )
    expect(await screen.findByText(`Added "CDE2313 Section A". UniFlow's number will join it soon.`)).toBeTruthy()
    expect(sourcesApi.createSource).not.toHaveBeenCalled()
  })

  it('shows a group waiting for UniFlow to join', async () => {
    vi.mocked(sourcesApi.getMySources).mockResolvedValue([
      { ...group, platform: 'whatsapp_group', platform_label: 'WhatsApp group', status: 'pending', message_count: 0 },
    ])
    renderPage()
    expect(await screen.findByText('WhatsApp group · 0 messages')).toBeTruthy()
    expect(screen.getByText('Waiting to join')).toBeTruthy()
  })

  it("adds a group without a link, for me to add UniFlow's number to", async () => {
    vi.mocked(sourcesApi.connectSource).mockResolvedValue({
      ...group,
      id: 10,
      title: 'HCI C2',
      platform: 'whatsapp_group',
      platform_label: 'WhatsApp group',
      status: 'pending',
      message_count: 0,
      added_by_number: true,
      uniflow_number: '+60123456789',
    })
    renderPage()

    fireEvent.change(await screen.findByLabelText('Group name'), { target: { value: 'HCI C2' } })
    fireEvent.click(screen.getByRole('radio', { name: "I'll add UniFlow's number" }))
    expect(screen.queryByLabelText('WhatsApp invite link')).toBeNull()
    expect(screen.getByLabelText('Group name').getAttribute('aria-describedby')).toBe('group-name-hint')
    expect(screen.getByText(/exactly as it shows in WhatsApp/)).toBeTruthy()
    fireEvent.click(screen.getByRole('button', { name: 'Add group' }))

    await waitFor(() => expect(sourcesApi.connectSource).toHaveBeenCalledWith('', 'HCI C2'))
    expect(await screen.findByText(`Added "HCI C2". Now add UniFlow's number to the group in WhatsApp: see the steps below.`)).toBeTruthy()
  })

  it('needs the invite link when that is the chosen way', async () => {
    renderPage()
    fireEvent.change(await screen.findByLabelText('Group name'), { target: { value: 'HCI C2' } })
    expect((screen.getByRole('button', { name: 'Add group' }) as HTMLButtonElement).disabled).toBe(true)
    expect(screen.getByText('Paste the invite link, or choose another way.')).toBeTruthy()
  })

  const waiting: Source = {
    ...group,
    platform: 'whatsapp_group',
    platform_label: 'WhatsApp group',
    status: 'pending',
    message_count: 0,
    added_by_number: true,
    uniflow_number: '+60123456789',
  }

  it("shows UniFlow's number and the steps for a group I'm adding by number", async () => {
    const writeText = vi.fn().mockResolvedValue(undefined)
    Object.assign(navigator, { clipboard: { writeText } })
    vi.mocked(sourcesApi.getMySources).mockResolvedValue([waiting])
    renderPage()

    expect(await screen.findByText('+60123456789')).toBeTruthy()
    expect(screen.getByText(/recognises the group by its name, "CDE2313 Sec A"/)).toBeTruthy()
    expect(screen.getByRole('link', { name: 'what UniFlow reads' }).getAttribute('href')).toBe('/privacy')
    fireEvent.click(screen.getByRole('button', { name: 'Copy number' }))
    await waitFor(() => expect(writeText).toHaveBeenCalledWith('+60123456789'))
    expect(await screen.findByRole('button', { name: 'Copied' })).toBeTruthy()
  })

  it('lets me pick my group if UniFlow joined it under another name', async () => {
    vi.mocked(sourcesApi.getMySources).mockResolvedValue([waiting])
    vi.mocked(sourcesApi.getUnclaimedGroups).mockResolvedValue([
      { id: 30, title: 'CDE2313 Section A (official)', joined_at: '2026-10-19T01:10:00Z' },
    ])
    vi.mocked(sourcesApi.claimGroup).mockResolvedValue({ ...waiting, id: 30, status: 'active' })
    renderPage()

    fireEvent.click(await screen.findByRole('button', { name: 'This is my group: CDE2313 Section A (official)' }))

    await waitFor(() => expect(sourcesApi.claimGroup).toHaveBeenCalledWith(7, 30))
    await waitFor(() => expect(sourcesApi.getMySources).toHaveBeenCalledTimes(2)) // my groups reloaded
  })

  it('says when a group is disconnected', async () => {
    vi.mocked(sourcesApi.getMySources).mockResolvedValue([
      { ...group, platform: 'telegram_channel', platform_label: 'Telegram channel', status: 'disconnected' },
    ])
    renderPage()
    expect(await screen.findByText('Disconnected')).toBeTruthy()
    expect(screen.getByText('New messages from this group are ignored.')).toBeTruthy()
  })

  it('explains why Add group is not available yet', async () => {
    renderPage()
    const button = await screen.findByRole('button', { name: 'Add group' })
    expect((button as HTMLButtonElement).disabled).toBe(true)
    expect(button.getAttribute('aria-describedby')).toBe('add-group-hint')
    expect(screen.getByText('Type a group name first.')).toBeTruthy()
  })

  it("explains a link UniFlow can't use", async () => {
    vi.mocked(sourcesApi.connectSource).mockRejectedValue(
      new ApiError({
        status: 400,
        code: 'validation_error',
        message: 'Invalid input.',
        fields: { invite_url: ["UniFlow can't join Telegram groups by link. Ask the group's admin to add the UniFlow bot…"] },
      }),
    )
    renderPage()

    fireEvent.change(await screen.findByLabelText('Group name'), { target: { value: 'SCI channel' } })
    fireEvent.change(screen.getByLabelText('WhatsApp invite link'), { target: { value: 'https://t.me/+abc' } })
    fireEvent.click(screen.getByRole('button', { name: 'Add group' }))

    expect(await screen.findByText(/add the UniFlow bot/, { selector: '[role="alert"]' })).toBeTruthy()
  })

  it('removes a group from my list after I confirm', async () => {
    vi.mocked(sourcesApi.leaveSource).mockResolvedValue()
    renderPage()

    fireEvent.click(await screen.findByRole('button', { name: 'Remove CDE2313 Sec A from my groups' }))
    expect(screen.getByText(/Other students who added it keep it/)).toBeTruthy()
    expect(sourcesApi.leaveSource).not.toHaveBeenCalled()

    vi.mocked(sourcesApi.getMySources).mockResolvedValue([])
    fireEvent.click(screen.getByRole('button', { name: 'Remove' }))

    await waitFor(() => expect(sourcesApi.leaveSource).toHaveBeenCalledWith(7))
    expect(await screen.findByText('No groups yet')).toBeTruthy()
  })

  it('keeps the group when I cancel removing it', async () => {
    renderPage()

    fireEvent.click(await screen.findByRole('button', { name: 'Remove CDE2313 Sec A from my groups' }))
    fireEvent.click(screen.getByRole('button', { name: 'Cancel' }))

    expect(screen.queryByText(/Other students who added it keep it/)).toBeNull()
    expect(sourcesApi.leaveSource).not.toHaveBeenCalled()
  })

  it('pastes messages and says how many were new', async () => {
    vi.mocked(sourcesApi.pasteMessages).mockResolvedValue({ added: 2, already_stored: 1 })
    renderPage()

    await chooseFromMenu('Paste messages')
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

    await chooseFromMenu('Upload WhatsApp export')
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

    await chooseFromMenu('Upload WhatsApp export')
    const file = new File(['%PDF'], 'chat.pdf')
    fireEvent.change(screen.getByLabelText('WhatsApp export (.txt)'), { target: { files: [file] } })
    fireEvent.click(screen.getByRole('button', { name: 'Upload' }))

    expect(await screen.findByText('Upload the .txt file from WhatsApp\'s "Export chat".')).toBeTruthy()
  })
})
