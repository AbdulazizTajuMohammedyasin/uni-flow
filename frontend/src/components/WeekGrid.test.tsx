import { render, screen, within } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'

import type { ClassSlot, TimetableDays } from '@/types/timetable'

import { WeekGrid } from './WeekGrid'

function slot(overrides: Partial<ClassSlot>): ClassSlot {
  return {
    section_id: 1,
    course_code: 'CCS2213',
    course_name: 'Machine Learning',
    section_code: 'C2',
    lecturer_name: '',
    start_time: '08:30',
    end_time: '10:30',
    meeting_type: 'lecture',
    building: '',
    room: 'B09_210',
    change: null,
    ...overrides,
  }
}

const dates = ['2026-10-19', '2026-10-20', '2026-10-21', '2026-10-22', '2026-10-23', '2026-10-24', '2026-10-25']
const days: TimetableDays['days'] = dates.map((date, weekday) => ({
  date,
  weekday,
  classes:
    weekday === 0
      ? [slot({}), slot({ section_id: 2, course_code: 'CCS2223', start_time: '14:30', end_time: '16:30', change: { id: 9, kind: 'class_moved', status: 'pending' } })]
      : weekday === 4
        ? [slot({ section_id: 3, course_code: 'CCC2123', start_time: '20:30', end_time: '23:30' })]
        : [],
}))

afterEach(() => {
  vi.useRealTimers()
})

describe('WeekGrid', () => {
  it('lays the week out like AIU: days down the side, hours across', () => {
    render(<WeekGrid days={days} today="2026-10-19" />)

    const rows = screen.getAllByRole('rowheader').map((cell) => cell.textContent)
    expect(rows).toEqual(['MonToday', 'Tue20 Oct', 'Wed21 Oct', 'Thu22 Oct', 'Fri23 Oct', 'Sat24 Oct', 'Sun25 Oct'])
    // 08:30 … 22:30, widened by one hour for the class ending at 23:30.
    expect(screen.getByText('08:30', { selector: 'span.flex-1' })).toBeTruthy()
    expect(screen.getByText('22:30', { selector: 'span.flex-1' })).toBeTruthy()

    const monday = screen.getAllByRole('row')[1]
    expect(within(monday).getByText('CCS2213 · C2')).toBeTruthy()
    expect(within(monday).getByText('Change waiting')).toBeTruthy()
  })

  it('marks the class happening now', () => {
    vi.useFakeTimers({ toFake: ['Date'] })
    vi.setSystemTime(new Date('2026-10-19T09:30:00+08:00'))
    render(<WeekGrid days={days} today="2026-10-19" />)

    const now = screen.getByText('Now')
    expect(now.closest('li')?.textContent).toContain('CCS2213')
  })
})
