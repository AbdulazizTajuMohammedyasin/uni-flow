// Runs before every test file (configured in vite.config.ts → test.setupFiles).
import { cleanup } from '@testing-library/react'
import { afterEach } from 'vitest'

// Remove whatever a test rendered, so tests never affect each other.
afterEach(() => {
  cleanup()
})
