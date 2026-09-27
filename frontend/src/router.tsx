import { createBrowserRouter, type RouteObject } from 'react-router'

import { PageLoading } from '@/components/PageLoading'

import { NotFoundPage } from './pages/NotFound/NotFound'
import { PlaceholderPage } from './pages/Placeholder/Placeholder'
import { RouteErrorPage } from './pages/RouteError/RouteError'

/**
 * Builds the app's route tree. Layouts are lazy-loaded, so each area's code downloads
 * only when it is visited (students never download the staff dashboard).
 * Placeholder pages are replaced by real feature pages in later milestones.
 *
 * A function (not a shared constant) because React Router mutates route objects when
 * lazy routes resolve: every router must get its own fresh copy.
 */
export function createAppRoutes(): RouteObject[] {
  return [
    {
      // Pathless root: catches errors from every page and shows a loader on first load.
      errorElement: <RouteErrorPage />,
      hydrateFallbackElement: <PageLoading />,
      children: [
        {
          path: '/',
          lazy: { Component: async () => (await import('./components/AppLayout')).default },
          children: [
            { index: true, element: <PlaceholderPage title="Home" /> },
            { path: 'announcements', element: <PlaceholderPage title="Announcements" /> },
            { path: 'events', element: <PlaceholderPage title="Events" /> },
            { path: 'timetable', element: <PlaceholderPage title="Timetable" /> },
            { path: 'communities', element: <PlaceholderPage title="Communities" /> },
          ],
        },
        {
          path: '/login',
          lazy: { Component: async () => (await import('./components/AuthLayout')).default },
          children: [
            {
              index: true,
              element: <PlaceholderPage title="Log in" description="Login arrives in M1." />,
            },
          ],
        },
        {
          path: '/staff',
          lazy: { Component: async () => (await import('./components/StaffLayout')).default },
          children: [{ index: true, element: <PlaceholderPage title="Staff dashboard" /> }],
        },
        { path: '*', element: <NotFoundPage /> },
      ],
    },
  ]
}

/** The app's router (main.tsx). Tests build their own with createAppRoutes(). */
export const router = createBrowserRouter(createAppRoutes())
