import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import App from './App'

describe('App placeholder', () => {
  it('shows the UniFlow heading and tagline', () => {
    render(<App />)

    // getBy* throws if the element is missing, so finding it is the assertion.
    const heading = screen.getByRole('heading', { level: 1, name: 'UniFlow' })
    expect(heading).toBeTruthy()
    expect(screen.getByText('Your campus information in one place.')).toBeTruthy()
  })
})
