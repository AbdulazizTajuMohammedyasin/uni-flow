import { fireEvent, render, screen } from '@testing-library/react'
import { beforeEach, describe, expect, it } from 'vitest'

import { ThemeToggle } from './ThemeToggle'

beforeEach(() => {
  localStorage.clear()
  document.documentElement.classList.remove('dark')
})

describe('ThemeToggle', () => {
  it('shows the three choices with "System" selected at first', () => {
    render(<ThemeToggle />)
    expect(screen.getByRole('radiogroup', { name: 'Theme' })).toBeTruthy()
    expect(screen.getByRole('radio', { name: 'System' }).getAttribute('aria-checked')).toBe('true')
    expect(screen.getByRole('radio', { name: 'Dark' }).getAttribute('aria-checked')).toBe('false')
  })

  it('switches to dark and back to light', () => {
    render(<ThemeToggle />)
    fireEvent.click(screen.getByRole('radio', { name: 'Dark' }))
    expect(document.documentElement.classList.contains('dark')).toBe(true)
    expect(screen.getByRole('radio', { name: 'Dark' }).getAttribute('aria-checked')).toBe('true')

    fireEvent.click(screen.getByRole('radio', { name: 'Light' }))
    expect(document.documentElement.classList.contains('dark')).toBe(false)
  })
})
