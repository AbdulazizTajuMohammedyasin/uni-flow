import { ChevronsUpDown, LayoutDashboard, LogOut, Shield, UserRound } from 'lucide-react'
import { Link, useNavigate } from 'react-router'

import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { useAuth } from '@/context/AuthContext'
import { canUseStaffArea } from '@/lib/capabilities'
import { cn } from '@/lib/utils'

/** "Aisha Rahman" -> "AR" (at most two letters). */
function initials(name: string): string {
  return name
    .split(' ')
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0].toUpperCase())
    .join('')
}

const itemClass = 'min-h-11 gap-2.5 px-2.5 md:min-h-9'

/**
 * Who is logged in, with Profile, the privacy notice, the staff dashboard (staff only) and
 * Log out. "full" (desktop sidebar) shows the name and email; "compact" (phone top bar) only
 * the initials.
 */
export function AccountMenu({ variant }: { variant: 'full' | 'compact' }) {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  if (!user) return null

  async function handleLogout() {
    await logout()
    navigate('/login', { replace: true })
  }

  return (
    <DropdownMenu>
      <DropdownMenuTrigger
        aria-label="Account menu"
        className={cn(
          'flex items-center gap-3 rounded-lg text-left outline-none focus-visible:ring-3 focus-visible:ring-ring/50',
          variant === 'full' ? 'w-full p-2 hover:bg-muted' : 'size-11 justify-center',
        )}
      >
        <span
          aria-hidden
          className="flex size-8 shrink-0 items-center justify-center rounded-full bg-primary text-xs font-semibold text-primary-foreground"
        >
          {initials(user.full_name)}
        </span>
        {variant === 'full' && (
          <>
            <span className="min-w-0 flex-1">
              <span className="block truncate text-sm font-medium">{user.full_name}</span>
              <span className="block truncate text-xs text-muted-foreground">{user.email}</span>
            </span>
            <ChevronsUpDown aria-hidden className="size-4 shrink-0 text-muted-foreground" />
          </>
        )}
      </DropdownMenuTrigger>

      {/* Sidebar: as wide as the account card it opens from. Phone: a fixed width under the initials. */}
      <DropdownMenuContent
        align="end"
        side={variant === 'full' ? 'top' : 'bottom'}
        className={variant === 'full' ? 'w-(--radix-dropdown-menu-trigger-width)' : 'w-64'}
      >
        <DropdownMenuLabel className="px-2.5 py-2">
          <span className="block truncate text-sm font-medium text-foreground">{user.full_name}</span>
          <span className="block truncate text-xs font-normal text-muted-foreground">{user.email}</span>
        </DropdownMenuLabel>
        <DropdownMenuSeparator />
        <DropdownMenuItem asChild className={itemClass}>
          <Link to="/profile">
            <UserRound aria-hidden />
            Profile
          </Link>
        </DropdownMenuItem>
        <DropdownMenuItem asChild className={itemClass}>
          <Link to="/privacy">
            <Shield aria-hidden />
            Privacy notice
          </Link>
        </DropdownMenuItem>
        {canUseStaffArea(user) && (
          <DropdownMenuItem asChild className={itemClass}>
            <Link to="/staff">
              <LayoutDashboard aria-hidden />
              Staff dashboard
            </Link>
          </DropdownMenuItem>
        )}
        <DropdownMenuSeparator />
        <DropdownMenuItem className={itemClass} onSelect={handleLogout}>
          <LogOut aria-hidden />
          Log out
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
