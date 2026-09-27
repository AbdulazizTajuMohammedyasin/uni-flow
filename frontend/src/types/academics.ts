/** GET /api/v1/academics/... (active items only) */
export type School = { id: number; code: string; name: string }

export type Programme = {
  id: number
  code: string
  name: string
  level: string
  level_label: string
  school: number
}

export type Intake = { id: number; code: string; name: string; start_date: string }
