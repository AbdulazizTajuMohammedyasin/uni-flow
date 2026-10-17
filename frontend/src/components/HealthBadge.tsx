import { Badge } from '@/components/ui/badge'
import { useHealth } from '@/hooks/useHealth'

/**
 * Development-only indicator: does the website reach the Django API (and the database)?
 * Rendered only when `import.meta.env.DEV` is true (see AppLayout).
 */
export function HealthBadge() {
  const { data, isPending, isError } = useHealth()

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
  return <Badge className="bg-success text-background">API: ok</Badge>
}
