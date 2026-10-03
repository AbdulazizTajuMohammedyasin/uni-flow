import { createBrowserRouter, type RouteObject } from 'react-router'

import { PageLoading } from '@/components/PageLoading'
import { RequireAuth } from '@/components/RequireAuth'
import { RequireCapability } from '@/components/RequireCapability'
import { staffNavItems } from '@/lib/navigation'

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
          // Login-only area: visitors who are not logged in are sent to /login.
          element: <RequireAuth />,
          children: [
            {
              path: '/',
              lazy: { Component: async () => (await import('./components/AppLayout')).default },
              children: [
                { index: true, element: <PlaceholderPage title="Home" /> },
                { path: 'announcements', element: <PlaceholderPage title="Announcements" /> },
                { path: 'events', element: <PlaceholderPage title="Events" /> },
                {
                  path: 'timetable',
                  lazy: {
                    Component: async () => (await import('./pages/Timetable/Timetable')).TimetablePage,
                  },
                },
                { path: 'communities', element: <PlaceholderPage title="Communities" /> },
                {
                  path: 'profile',
                  lazy: { Component: async () => (await import('./pages/Profile/Profile')).ProfilePage },
                },
              ],
            },
            {
              // Students choose their school/programme/intake here (centred-card frame).
              lazy: { Component: async () => (await import('./components/AuthLayout')).default },
              children: [
                {
                  path: '/onboarding',
                  lazy: {
                    Component: async () =>
                      (await import('./pages/Onboarding/Onboarding')).OnboardingPage,
                  },
                },
              ],
            },
            {
              // Staff dashboard: only for users with at least one "*.manage" capability.
              path: '/staff',
              element: <RequireCapability />,
              children: [
                {
                  lazy: {
                    Component: async () => (await import('./components/StaffLayout')).default,
                  },
                  children: [
                    { index: true, element: <PlaceholderPage title="Staff dashboard" /> },
                    // Each section checks its own capability ("No access" page otherwise).
                    ...staffNavItems
                      .filter((item) => item.cap)
                      .map((item) => ({
                        path: item.to.replace('/staff/', ''),
                        element: <RequireCapability cap={item.cap} />,
                        children: [{ index: true, element: <PlaceholderPage title={item.label} /> }],
                      })),
                  ],
                },
              ],
            },
          ],
        },
        {
          // Public pages in the centred-card frame.
          lazy: { Component: async () => (await import('./components/AuthLayout')).default },
          children: [
            // Loaded only when visited (keeps the form libraries out of the main download).
            {
              path: '/login',
              lazy: { Component: async () => (await import('./pages/Login/Login')).LoginPage },
            },
            {
              path: '/register',
              lazy: {
                Component: async () => (await import('./pages/Register/Register')).RegisterPage,
              },
            },
            {
              path: '/verify-email/:uid/:token', // the link in the activation email
              lazy: {
                Component: async () =>
                  (await import('./pages/ActivateAccount/ActivateAccount')).ActivateAccountPage,
              },
            },
            {
              path: '/forgot-password',
              lazy: {
                Component: async () =>
                  (await import('./pages/ForgotPassword/ForgotPassword')).ForgotPasswordPage,
              },
            },
            {
              path: '/reset-password/:uid/:token', // the link in the reset email
              lazy: {
                Component: async () =>
                  (await import('./pages/ResetPassword/ResetPassword')).ResetPasswordPage,
              },
            },
          ],
        },
        { path: '*', element: <NotFoundPage /> },
      ],
    },
  ]
}

/** The app's router (main.tsx). Tests build their own with createAppRoutes(). */
export const router = createBrowserRouter(createAppRoutes())
