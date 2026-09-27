// Runs before every test file (configured in vite.config.ts → test.setupFiles).
import { cleanup, configure } from '@testing-library/react'
import { afterEach } from 'vitest'

// Wait up to 3 s (default 1 s) for things to appear: lazy pages load slower on busy machines.
configure({ asyncUtilTimeout: 3000 })

// Remove whatever a test rendered, so tests never affect each other.
afterEach(() => {
  cleanup()
})
