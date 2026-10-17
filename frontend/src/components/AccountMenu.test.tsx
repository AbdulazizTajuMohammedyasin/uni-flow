import { fireEvent, render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { useAuth } from '@/context/AuthContext'
import { makeSchoolStaff, makeStudent } from '@/test/fixtures'
import type { User } from '@/types/auth'

import { AccountMenu } from './AccountMenu'

vi.mock('@/context/AuthContext', () => ({ useAuth: vi.fn() }))

const logout = vi.fn()

function renderAs(user: User) {
  vi.mocked(useAuth).mockReturnValue({ user, logout, isLoading: false, login: vi.fn(), setUser: vi.fn() })
  render(
    <MemoryRouter>
      <AccountMenu variant="full" />
    </MemoryRouter>,
  )
  // Radix menus open from the keyboard (jsdom has no pointer events).
  fireEvent.keyDown(screen.getByRole('button', { name: 'Account menu' }), { key: 'Enter' })
}

beforeEach(() => {
  logout.mockReset().mockResolvedValue(undefined)
})

describe('AccountMenu', () => {
  it("shows the student's name and the account links", async () => {
    renderAs(makeStudent({ full_name: 'Aisha Rahman' }))

    expect(screen.getAllByText('Aisha Rahman').length).toBeGreaterThan(0)
    expect(await screen.findByRole('menuitem', { name: 'Profile' })).toBeTruthy()
    expect(screen.getByRole('menuitem', { name: 'Privacy notice' })).toBeTruthy()
    expect(screen.getByRole('menuitem', { name: 'Log out' })).toBeTruthy()
    expect(screen.queryByRole('menuitem', { name: 'Staff dashboard' })).toBeNull()
  })

  it('offers the staff dashboard to staff', async () => {
    renderAs(makeSchoolStaff())
    expect(await screen.findByRole('menuitem', { name: 'Staff dashboard' })).toBeTruthy()
  })

  it('logs out', async () => {
    renderAs(makeStudent())
    fireEvent.click(await screen.findByRole('menuitem', { name: 'Log out' }))
    expect(logout).toHaveBeenCalled()
  })
})
