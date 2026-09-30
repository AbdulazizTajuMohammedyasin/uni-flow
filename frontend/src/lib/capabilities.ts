import type { Capability, User } from '@/types/auth'

/**
 * Permission helpers. They only decide what the website *shows*: the backend checks
 * every action again, so hiding a button is a convenience, not the security.
 */
export function can(user: User | null, capability: Capability): boolean {
  return Boolean(user?.capabilities?.[capability])
}

/** Staff dashboard access: at least one "*.manage" capability. */
export function canUseStaffArea(user: User | null): boolean {
  return Object.values(user?.capabilities ?? {}).some(Boolean)
}
