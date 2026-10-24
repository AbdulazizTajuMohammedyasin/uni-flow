import { QueryClientProvider } from '@tanstack/react-query'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { ApiError } from '@/api/errors'
import * as timetableApi from '@/api/timetable'
import { createQueryClient } from '@/lib/queryClient'
import type { ImportRow, TimetableImport } from '@/types/timetable'

import { TimetableImportBox } from './TimetableImport'

vi.mock('@/api/timetable', () => ({
  startImport: vi.fn(),
  getImport: vi.fn(),
  chooseImportTab: vi.fn(),
  confirmImport: vi.fn(),
  discardImport: vi.fn(),
}))

const cde: ImportRow = {
  course_code: 'CDE2313',
  course_name: 'Data Structures',
  section: 'A',
  lecturer: 'Dr Lee',
  meetings: [{ day: 'monday', start: '10:00', end: '12:00', type: 'lecture', room: 'B2' }],
}
const mth: ImportRow = {
  course_code: 'MTH1013',
  course_name: 'Discrete Maths',
  section: 'G1',
  lecturer: '',
  meetings: [{ day: 'tuesday', start: '08:00', end: '10:00', type: 'tutorial', room: 'A1-04' }],
}

const ready: TimetableImport = {
  id: 3,
  status: 'ready',
  file_name: 'SCI timetable.xlsx',
  group: '',
  tab: 'BCS Oct 2025',
  tabs: ['BBA Mar 2025', 'BCS Oct 2025'],
  rows: [cde, mth],
  report: {},
  error: '',
  created_at: '2025-11-01T00:00:00Z',
}

function renderBox() {
  render(
    <QueryClientProvider client={createQueryClient()}>
      <TimetableImportBox />
    </QueryClientProvider>,
  )
}

function uploadFile() {
  const file = new File(['xlsx'], 'SCI timetable.xlsx')
  fireEvent.change(screen.getByLabelText('Timetable file'), { target: { files: [file] } })
  fireEvent.click(screen.getByRole('button', { name: 'Read timetable' }))
  return file
}

beforeEach(() => {
  vi.mocked(timetableApi.startImport).mockResolvedValue({ ...ready, status: 'reading', rows: [] })
  vi.mocked(timetableApi.getImport).mockResolvedValue(ready)
})

describe('Add my timetable', () => {
  it('reads an uploaded file and asks "Is this your timetable?"', async () => {
    renderBox()
    const file = uploadFile()

    expect(await screen.findByText('Is this your timetable?')).toBeTruthy()
    expect(timetableApi.startImport).toHaveBeenCalledWith({ file }, 'current')
    expect(screen.getByText('CDE2313 · Section A')).toBeTruthy()
    expect(screen.getByText('Mon 10:00–12:00 · B2')).toBeTruthy()
    expect((screen.getByLabelText('Tab') as HTMLSelectElement).value).toBe('BCS Oct 2025')
  })

  it('confirms only the classes the student keeps', async () => {
    vi.mocked(timetableApi.confirmImport).mockResolvedValue({
      ...ready,
      status: 'confirmed',
      report: { enrolled: ['CDE2313 Section A'] },
    })
    renderBox()
    uploadFile()

    fireEvent.click(await screen.findByRole('checkbox', { name: /MTH1013/ }))
    fireEvent.click(screen.getByRole('button', { name: 'Confirm 1 class' }))

    await waitFor(() => expect(timetableApi.confirmImport).toHaveBeenCalledWith(3, [cde]))
  })

  it('switches to another tab', async () => {
    vi.mocked(timetableApi.chooseImportTab).mockResolvedValue({ ...ready, tab: 'BBA Mar 2025' })
    renderBox()
    uploadFile()

    fireEvent.change(await screen.findByLabelText('Tab'), { target: { value: 'BBA Mar 2025' } })
    await waitFor(() => expect(timetableApi.chooseImportTab).toHaveBeenCalledWith(3, 'BBA Mar 2025'))
  })

  it('can say "Not my timetable"', async () => {
    vi.mocked(timetableApi.discardImport).mockResolvedValue({ ...ready, status: 'discarded' })
    renderBox()
    uploadFile()

    fireEvent.click(await screen.findByRole('button', { name: 'Not my timetable' }))
    await waitFor(() => expect(timetableApi.discardImport).toHaveBeenCalledWith(3))
    expect(await screen.findByLabelText('Timetable file')).toBeTruthy() // back to the start
  })

  it("explains a link that only opens with an AIU account", async () => {
    vi.mocked(timetableApi.startImport).mockRejectedValue(
      new ApiError({
        status: 400,
        code: 'validation_error',
        message: 'Invalid input.',
        fields: { link: ['UniFlow couldn\'t open this link. … File → Download → Microsoft Excel (.xlsx) …'] },
      }),
    )
    renderBox()

    fireEvent.change(screen.getByLabelText('…or a Google Drive / Sheets link'), {
      target: { value: 'https://docs.google.com/spreadsheets/d/1Uy5/edit' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Read link' }))

    expect(await screen.findByText(/File → Download → Microsoft Excel/, { selector: '[role="alert"]' })).toBeTruthy()
  })

  it('shows why a file could not be read', async () => {
    vi.mocked(timetableApi.getImport).mockResolvedValue({
      ...ready,
      status: 'failed',
      error: 'No classes were found in this file.',
    })
    renderBox()
    uploadFile()

    expect(await screen.findByText('No classes were found in this file.')).toBeTruthy()
    expect(screen.getByRole('button', { name: 'Try another file' })).toBeTruthy()
  })
})
