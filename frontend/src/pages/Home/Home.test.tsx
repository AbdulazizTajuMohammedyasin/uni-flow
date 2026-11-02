import { render, screen, within } from '@testing-library/react'
import { createMemoryRouter, RouterProvider } from 'react-router'
import { describe, expect, it } from 'vitest'

import { HomePage } from './Home'

function renderPage() {
  const router = createMemoryRouter([{ path: '/', element: <HomePage /> }])
  render(<RouterProvider router={router} />)
}

describe('Home page', () => {
  it('explains how to use UniFlow in four steps', async () => {
    renderPage()

    const heading = await screen.findByRole('heading', { level: 2, name: 'How to use UniFlow' })
    const list = heading.closest('section')!.querySelector('ol')!
    const steps = within(list).getAllByRole('listitem')
    expect(steps).toHaveLength(4)
    expect(steps[0].textContent).toContain('@student.aiu.edu.my')
  })

  it('links the top navigation to sections on the page', async () => {
    renderPage()

    const nav = await screen.findByRole('navigation', { name: 'Home page' })
    expect(within(nav).getByRole('link', { name: 'How it works' }).getAttribute('href')).toBe('#how-it-works')
    expect(within(nav).getByRole('link', { name: 'Features' }).getAttribute('href')).toBe('#features')
    expect(document.getElementById('how-it-works')).toBeTruthy()
    expect(document.getElementById('features')).toBeTruthy()
  })

  it('gives every screenshot a description', async () => {
    renderPage()

    const images = await screen.findAllByRole('img')
    expect(images.length).toBeGreaterThan(0)
    for (const image of images) {
      expect(image.getAttribute('alt')?.trim()).toBeTruthy()
    }
  })

  it('links to the privacy notice', async () => {
    renderPage()

    const links = await screen.findAllByRole('link', { name: /privacy notice/i })
    expect(links.some((link) => link.getAttribute('href') === '/privacy')).toBe(true)
  })

  it('has exactly one h1', async () => {
    renderPage()

    await screen.findByRole('heading', { level: 2, name: 'Ready to start?' })
    expect(screen.getAllByRole('heading', { level: 1 })).toHaveLength(1)
  })
})
