import { Compass } from 'lucide-react'
import { Link } from 'react-router'

import { StatusMessage } from '@/components/StatusMessage'
import { Button } from '@/components/ui/button'

/** Shown for any address that does not match a route. */
export function NotFoundPage() {
  return (
    <main className="flex min-h-screen items-center justify-center px-4 py-10">
      <StatusMessage
        icon={Compass}
        code="404"
        title="Page not found"
        action={
          <Button asChild size="lg">
            <Link to="/">Go to home</Link>
          </Button>
        }
      >
        The page you are looking for does not exist.
      </StatusMessage>
    </main>
  )
}
