import { QueryClientProvider } from '@tanstack/react-query'
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { RouterProvider } from 'react-router/dom'

import { AuthProvider } from './context/AuthContext'
import './index.css'
import { createQueryClient } from './lib/queryClient'
import { applyTheme, followSystemTheme } from './lib/theme'
import { router } from './router'

const queryClient = createQueryClient()

// index.html already set light or dark; keep "System" in step with the device from now on.
applyTheme()
followSystemTheme()

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <RouterProvider router={router} />
      </AuthProvider>
    </QueryClientProvider>
  </StrictMode>,
)
