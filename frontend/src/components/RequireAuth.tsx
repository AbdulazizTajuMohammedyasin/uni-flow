import { Navigate, Outlet, useLocation } from 'react-router'

import { useAuth } from '@/context/AuthContext'

import { PageLoading } from './PageLoading'

/** Wraps login-only routes: visitors who are not logged in are sent to /login?next=... */
export function RequireAuth() {
  const { user, isLoading } = useAuth()
  const location = useLocation()

  if (isLoading) {
    return <PageLoading />
  }
  if (!user) {
    const next = encodeURIComponent(location.pathname + location.search)
    return <Navigate to={`/login?next=${next}`} replace />
  }
  return <Outlet />
}
