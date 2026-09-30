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
  return allowed ? <Outlet /> : <NoAccessPage />
}
