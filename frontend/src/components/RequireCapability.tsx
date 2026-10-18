import { Outlet } from 'react-router'

import { useAuth } from '@/context/AuthContext'
import { can, canUseStaffArea } from '@/lib/capabilities'
import { NoAccessPage } from '@/pages/NoAccess/NoAccess'
import type { Capability } from '@/types/auth'

type RequireCapabilityProps = {
  /** Leave out to allow anyone who can use the staff area. */
  cap?: Capability
}

/** Route guard: shows the "No access" page when the capability is missing. */
export function RequireCapability({ cap }: RequireCapabilityProps) {
  const { user } = useAuth()
  const allowed = cap ? can(user, cap) : canUseStaffArea(user)
  if (allowed) return <Outlet />
  // A section inside the staff area already sits in the layout's <main>; the staff area itself
  // has no layout around it yet, so there the message is the page's main content.
  return cap ? (
    <NoAccessPage />
  ) : (
    <main>
      <NoAccessPage />
    </main>
  )
}
