import { useState, type FormEvent } from 'react'
import { Search } from 'lucide-react'
import { useSearchParams } from 'react-router'

import { EmptyState } from '@/components/EmptyState'
import { ErrorState } from '@/components/ErrorState'
import { ItemList, ItemRow } from '@/components/ItemRow'
import { ListSkeleton } from '@/components/ListSkeleton'
import { PageHeader } from '@/components/PageHeader'
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
      <PageHeader title="Search" />
      <form onSubmit={onSubmit} role="search" className="space-y-1.5">
        <Label htmlFor="search-text">Search your items</Label>
        <div className="flex gap-2">
          <div className="relative flex-1">
            <Search aria-hidden className="pointer-events-none absolute top-1/2 left-3.5 size-5 -translate-y-1/2 text-muted-foreground" />
            <Input
              id="search-text"
              type="search"
              placeholder="e.g. Petronas internship"
              value={text}
              onChange={(event) => setText(event.target.value)}
              className="h-12 pl-11 text-base md:h-11 md:text-base"
            />
          </div>
          <Button type="submit" className="h-12 px-5 md:h-11" disabled={text.trim().length < 2}>
            Search
          </Button>
        </div>
      </form>

      {query.length < 2 ? (
        <p className="text-sm text-muted-foreground">
          Searches everything UniFlow showed you: titles, summaries, places and the original messages.
        </p>
      ) : results.isPending ? (
        <ListSkeleton />
      ) : results.isError ? (
        <ErrorState title="Could not search right now" />
      ) : results.data.length === 0 ? (
        <EmptyState title="Nothing found" description={`No items of yours mention "${query}".`} />
      ) : (
        <div className="space-y-2">
          <p role="status" className="text-sm text-muted-foreground">
            {results.data.length} result{results.data.length === 1 ? '' : 's'} for “{query}”
          </p>
          <ItemList>
            {results.data.map((item) => (
              <ItemRow key={item.id} item={item} />
            ))}
          </ItemList>
        </div>
      )}
    </div>
  )
}
