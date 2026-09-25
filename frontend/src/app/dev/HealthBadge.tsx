import { useQuery } from '@tanstack/react-query'

import { Badge } from '@/components/ui/badge'
import { getHealth } from '@/shared/api/health'

/**
 * Development-only indicator: does the website reach the Django API (and the database)?
 * Rendered only when `import.meta.env.DEV` is true (see AppLayout).
 */
export function HealthBadge() {
  const { data, isPending, isError } = useQuery({
    queryKey: ['health'],
    queryFn: getHealth,
    retry: false,
  })

  if (isPending) {
    return <Badge variant="secondary">API: checking…</Badge>
  }
  if (isError || data.status !== 'ok') {
    return (
      <Badge variant="destructive" title="Is the backend running? (pipenv run python manage.py runserver)">
        API: offline
      </Badge>
    )
  }
  return <Badge className="bg-emerald-600 text-white">API: ok</Badge>
}
