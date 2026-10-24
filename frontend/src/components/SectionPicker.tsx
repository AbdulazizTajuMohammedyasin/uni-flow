import { useEffect, useState } from 'react'

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { useJoinSection, useSectionSearch } from '@/hooks/useTimetable'
import { meetingText } from '@/lib/timetable'

import type { SemesterChoice } from '@/types/timetable'

import { ErrorState } from './ErrorState'

type Props = {
  /** Sections the student already has (shown as "Added"). */
  mySectionIds: number[]
  /** Whose sections: this semester's or the next one's. */
  semester?: SemesterChoice
}

/** Search this or next semester's sections by course code or name, and add them to "My sections". */
export function SectionPicker({ mySectionIds, semester = 'current' }: Props) {
  const [text, setText] = useState('')
  const [search, setSearch] = useState('')
  const sections = useSectionSearch(search, semester)
  const join = useJoinSection()

  // Wait until the student stops typing before searching.
  useEffect(() => {
    const timer = setTimeout(() => setSearch(text.trim()), 300)
    return () => clearTimeout(timer)
  }, [text])

  return (
    <div className="space-y-3">
      <Input
        aria-label="Search sections"
        placeholder="Search by course code or name, e.g. CDE2313"
        value={text}
        onChange={(event) => setText(event.target.value)}
      />

      {sections.isError && <ErrorState title="Could not load sections" />}
      {join.isError && (
        <p role="alert" className="text-sm text-destructive">
          {join.error.message}
        </p>
      )}

      <ul className="divide-y divide-border rounded-xl ring-1 ring-border">
        {sections.data?.results.map((section) => {
          const added = mySectionIds.includes(section.id)
          return (
            <li key={section.id} className="flex items-center justify-between gap-3 p-3">
              <div className="min-w-0">
                <p className="font-medium">
                  {section.course.code} · Section {section.code}
                </p>
                <p className="truncate text-sm text-muted-foreground">{section.course.name}</p>
                <p className="text-xs text-muted-foreground">
                  {section.meetings.map(meetingText).join(', ') || 'No weekly classes yet'}
                </p>
              </div>
              <Button
                size="sm"
                variant={added ? 'ghost' : 'outline'}
                disabled={added || join.isPending}
                onClick={() => join.mutate(section.id)}
                aria-label={`Add ${section.course.code} Section ${section.code}`}
              >
                {added ? 'Added' : 'Add'}
              </Button>
            </li>
          )
        })}
        {sections.data?.results.length === 0 && (
          <li className="p-3 text-sm text-muted-foreground">
            No sections found. You can add a missing class below.
          </li>
        )}
      </ul>
    </div>
  )
}
