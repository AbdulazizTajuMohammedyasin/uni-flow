import { Lock } from 'lucide-react'
import { Link } from 'react-router'

import { StatusMessage } from '@/components/StatusMessage'
import { Button } from '@/components/ui/button'

/** Shown when a logged-in user opens a page they are not allowed to use (403). */
export function NoAccessPage() {
  return (
    <section className="px-4 py-24">
      <StatusMessage
        icon={Lock}
        code="403"
        title="No access"
        action={
          <Button asChild size="lg">
            <Link to="/">Go to home</Link>
          </Button>
        }
      >
        Your account is not allowed to use this page. If you think this is a mistake, contact a UniFlow
        administrator.
      </StatusMessage>
    </section>
  )
}
