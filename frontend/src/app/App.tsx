import { createBrowserRouter } from 'react-router'
import { RouterProvider } from 'react-router/dom'

import { createAppRoutes } from './routes'

const router = createBrowserRouter(createAppRoutes())

/** Root component. App-wide providers (React Query, auth) are added here in later tasks. */
export default function App() {
  return <RouterProvider router={router} />
}
