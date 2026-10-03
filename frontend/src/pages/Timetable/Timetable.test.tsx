import { QueryClientProvider } from '@tanstack/react-query'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { createMemoryRouter, RouterProvider } from 'react-router'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import * as timetableApi from '@/api/timetable'
import { createQueryClient } from '@/lib/queryClient'
import type { Section, TimetableDays } from '@/types/timetable'

import { TimetablePage } from './Timetable'

vi.mock('@/api/timetable', () => ({
  getSections: vi.fn(),
  getMySections: vi.fn(),
  joinSection: vi.fn(),
  leaveSection: vi.fn(),
  addSectionByHand: vi.fn(),
  getToday: vi.fn(),
  getWeek: vi.fn(),
}))

const section: Section = {
  id: 5,
  course: { id: 1, code: 'CDE2313', name: 'Data Structures' },
  code: 'A',
  term: 2,
  lecturer_name: 'Dr Lee',
  source: 'admin',
  meetings: [
    {
      weekday: 0,
      weekday_label: 'Monday',
      start_time: '10:00:00',
      end_time: '12:00:00',
      meeting_type: 'lecture',
      building: '',
      room: 'B2',
    },
  ],
}

const slot = {
  section_id: 5,
  course_code: 'CDE2313',
  course_name: 'Data Structures',
  section_code: 'A',
  lecturer_name: 'Dr Lee',
  start_time: '10:00',
  end_time: '12:00',
  meeting_type: 'lecture' as const,
  building: '',
  room: 'B2',
}

function week(monday: string): TimetableDays {
  const days = Array.from({ length: 7 }, (_, index) => {
    const date = new Date(`${monday}T00:00:00Z`)
    date.setUTCDate(date.getUTCDate() + index)
    return { date: date.toISOString().slice(0, 10), weekday: index, classes: index === 0 ? [slot] : [] }
  })
  return { term: { id: 2, name: '2025/2026 Semester 2' }, days }
}

function renderTimetable(path = '/timetable') {
  const router = createMemoryRouter([{ path: '/timetable', element: <TimetablePage /> }], {
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
  vi.mocked(timetableApi.getMySections).mockResolvedValue([section])
  vi.mocked(timetableApi.getToday).mockResolvedValue({
    term: { id: 2, name: '2025/2026 Semester 2' },
    days: [{ date: '2026-03-30', weekday: 0, classes: [slot] }],
  })
  vi.mocked(timetableApi.getWeek).mockImplementation(async (date) => week(date ?? '2026-03-30'))
  vi.mocked(timetableApi.getSections).mockResolvedValue({
    count: 1,
    next: null,
    previous: null,
    results: [section],
  })
})

describe('Timetable page', () => {
  it("shows today's classes", async () => {
    renderTimetable()

    expect(await screen.findByText('10:00–12:00')).toBeTruthy()
    expect(screen.getByText('Monday 30 Mar')).toBeTruthy()
    expect(screen.getByText('Data Structures · B2')).toBeTruthy()
  })

  it('shows the week and moves to the next week', async () => {
    const router = renderTimetable()
    fireEvent.click(await screen.findByRole('button', { name: 'This week' }))

    expect(await screen.findByText('Sunday 5 Apr')).toBeTruthy()
    expect(router.state.location.search).toBe('?view=week')

    fireEvent.click(screen.getByRole('button', { name: 'Next week →' }))
    expect(await screen.findByText('Monday 6 Apr')).toBeTruthy()
    expect(timetableApi.getWeek).toHaveBeenLastCalledWith('2026-04-06')
  })

  it('offers to choose sections when the student has none, and adds one', async () => {
    vi.mocked(timetableApi.getMySections).mockResolvedValue([])
    vi.mocked(timetableApi.joinSection).mockResolvedValue(section)
    renderTimetable()

    expect(await screen.findByText("You haven't added your classes yet")).toBeTruthy()
    fireEvent.click(screen.getAllByRole('button', { name: 'Choose sections' })[0])
    fireEvent.click(await screen.findByRole('button', { name: 'Add CDE2313 Section A' }))

    await waitFor(() => expect(timetableApi.joinSection).toHaveBeenCalledWith(5))
  })

  it('searches sections as the student types', async () => {
    renderTimetable()
    fireEvent.click(await screen.findByRole('button', { name: 'Choose sections' }))
    fireEvent.change(screen.getByLabelText('Search sections'), { target: { value: 'cde' } })

    await waitFor(() => expect(timetableApi.getSections).toHaveBeenLastCalledWith('cde'))
    expect(await screen.findByRole('button', { name: 'Add CDE2313 Section A' })).toHaveProperty(
      'disabled',
      true, // already in "My sections"
    )
  })

  it('removes a section', async () => {
    vi.mocked(timetableApi.leaveSection).mockResolvedValue()
    renderTimetable()

    fireEvent.click(await screen.findByRole('button', { name: 'Remove CDE2313 Section A' }))
    await waitFor(() => expect(timetableApi.leaveSection).toHaveBeenCalledWith(5))
  })

  it('adds a missing class', async () => {
    vi.mocked(timetableApi.addSectionByHand).mockResolvedValue({
      ...section,
      id: 9,
      course: { id: 3, code: 'CDE3101', name: 'Operating Systems' },
    })
    renderTimetable()
    fireEvent.click(await screen.findByRole('button', { name: 'Add a missing class' }))

    fireEvent.change(screen.getByLabelText('Course code'), { target: { value: 'CDE3101' } })
    fireEvent.change(screen.getByLabelText('Course name'), { target: { value: 'Operating Systems' } })
    fireEvent.change(screen.getByLabelText('Section'), { target: { value: 'A' } })
    fireEvent.change(screen.getByLabelText('Day'), { target: { value: '2' } })
    fireEvent.change(screen.getByLabelText('Starts'), { target: { value: '14:00' } })
    fireEvent.change(screen.getByLabelText('Ends'), { target: { value: '16:00' } })
    fireEvent.change(screen.getByLabelText('Room'), { target: { value: 'C1' } })
    fireEvent.click(screen.getByRole('button', { name: 'Add class' }))

    expect(await screen.findByText('Added CDE3101 Section A to your timetable.')).toBeTruthy()
    expect(timetableApi.addSectionByHand).toHaveBeenCalledWith({
      course_code: 'CDE3101',
      course_name: 'Operating Systems',
      section: 'A',
      meetings: [
        {
          weekday: 2,
          start_time: '14:00',
          end_time: '16:00',
          meeting_type: 'lecture',
          room: 'C1',
          building: '',
        },
      ],
    })
  })

  it('checks that a class ends after it starts', async () => {
    renderTimetable()
    fireEvent.click(await screen.findByRole('button', { name: 'Add a missing class' }))

    fireEvent.change(screen.getByLabelText('Course code'), { target: { value: 'CDE3101' } })
    fireEvent.change(screen.getByLabelText('Course name'), { target: { value: 'OS' } })
    fireEvent.change(screen.getByLabelText('Section'), { target: { value: 'A' } })
    fireEvent.change(screen.getByLabelText('Starts'), { target: { value: '16:00' } })
    fireEvent.change(screen.getByLabelText('Ends'), { target: { value: '14:00' } })
    fireEvent.click(screen.getByRole('button', { name: 'Add class' }))

    expect(await screen.findByText('Must end after it starts.')).toBeTruthy()
    expect(timetableApi.addSectionByHand).not.toHaveBeenCalled()
  })
})
