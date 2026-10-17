import { ArrowLeft } from 'lucide-react'
import { Link, useLocation, useNavigate } from 'react-router'

/** Back to wherever I came from (Search, Notifications, …); For you when opened directly. */
export function BackLink() {
  const location = useLocation()
  const navigate = useNavigate()
  const className =
    'inline-flex min-h-11 items-center gap-1.5 rounded-md text-sm font-medium text-muted-foreground outline-none hover:text-foreground focus-visible:ring-3 focus-visible:ring-ring/50 md:min-h-8'
  if (location.key !== 'default') {
    return (
      <button type="button" onClick={() => navigate(-1)} className={className}>
        <ArrowLeft aria-hidden className="size-4" />
        Back
      </button>
    )
  }
  return (
    <Link to="/" className={className}>
      <ArrowLeft aria-hidden className="size-4" />
      For you
    </Link>
  )
}
