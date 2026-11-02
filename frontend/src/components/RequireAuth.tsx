import { lazy, Suspense } from 'react'
import { Navigate, Outlet, useLocation } from 'react-router'

import { useAuth } from '@/context/AuthContext'

import { PageLoading } from './PageLoading'

// Loaded only when a visitor opens the home page (students never download it).
const HomePage = lazy(async () => ({ default: (await import('@/pages/Home/Home')).HomePage }))

/**
 * Wraps login-only routes:
 * - visitors who are not logged in see the public home page at /, and are sent to
 *   /login?next=... from every other page
 * - students who have not chosen their school/programme/intake are sent to /onboarding
 */
export function RequireAuth() {
  const { user, isLoading } = useAuth()
  const location = useLocation()

  if (isLoading) {
    return <PageLoading />
  }
  if (!user) {
    if (location.pathname === '/') {
      return (
        <Suspense fallback={<PageLoading />}>
          <HomePage />
        </Suspense>
      )
    }
    const next = encodeURIComponent(location.pathname + location.search)
    return <Navigate to={`/login?next=${next}`} replace />
  }
  const needsOnboarding = user.role === 'student' && !user.profile_complete
  if (needsOnboarding && location.pathname !== '/onboarding') {
    return <Navigate to="/onboarding" replace />
  }
  return <Outlet />
}
