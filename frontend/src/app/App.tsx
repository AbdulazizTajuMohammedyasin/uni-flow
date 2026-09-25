import { createBrowserRouter } from 'react-router'
import { RouterProvider } from 'react-router/dom'

import { Providers } from './providers'
import { createAppRoutes } from './routes'

const router = createBrowserRouter(createAppRoutes())

/** Root component: app-wide providers around the router. */
export default function App() {
  return (
    <Providers>
      <RouterProvider router={router} />
    </Providers>
  )
}
