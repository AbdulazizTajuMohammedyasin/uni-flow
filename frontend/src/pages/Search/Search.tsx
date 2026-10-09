import { useState, type FormEvent } from 'react'
import { useSearchParams } from 'react-router'

import { EmptyState } from '@/components/EmptyState'
import { ErrorState } from '@/components/ErrorState'
import { FeedItemCard } from '@/components/FeedItemCard'
import { PageLoading } from '@/components/PageLoading'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { useSearch } from '@/hooks/useFeed'

/** /search?q= — find anything that was delivered to me (read or dismissed ones too). */
export function SearchPage() {
  const [params, setParams] = useSearchParams()
  const query = params.get('q') ?? ''
  const [text, setText] = useState(query)
  const results = useSearch(query)

  function onSubmit(event: FormEvent) {
    event.preventDefault()
    setParams(text.trim() ? { q: text.trim() } : {})
  }

  return (
    <div className="max-w-3xl space-y-6">
      <h1 className="text-2xl font-bold tracking-tight">Search</h1>
      <form onSubmit={onSubmit} role="search" className="flex items-end gap-2">
        <div className="flex-1 space-y-1.5">
          <Label htmlFor="search-text">Search your items</Label>
          <Input
            id="search-text"
            placeholder="e.g. Petronas internship"
            value={text}
            onChange={(event) => setText(event.target.value)}
          />
        </div>
        <Button type="submit" disabled={text.trim().length < 2}>
          Search
        </Button>
      </form>

      {query.length < 2 ? (
        <p className="text-sm text-muted-foreground">
          Searches everything UniFlow showed you: titles, summaries, places and the original messages.
        </p>
      ) : results.isPending ? (
        <PageLoading />
      ) : results.isError ? (
        <ErrorState title="Could not search right now" />
      ) : results.data.length === 0 ? (
        <EmptyState title="Nothing found" description={`No items of yours mention "${query}".`} />
      ) : (
        <ul className="space-y-2">
          {results.data.map((item) => (
            <FeedItemCard key={item.id} item={item} />
          ))}
        </ul>
      )}
    </div>
  )
}
