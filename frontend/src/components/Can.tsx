import type { ReactNode } from 'react'

import { useAuth } from '@/context/AuthContext'
import { can } from '@/lib/capabilities'
import type { Capability } from '@/types/auth'

type CanProps = {
  cap: Capability
  children: ReactNode
}

/** Shows its children only if the user has the capability: <Can cap="users.manage">…</Can> */
export function Can({ cap, children }: CanProps) {
  const { user } = useAuth()
  return can(user, cap) ? children : null
}
