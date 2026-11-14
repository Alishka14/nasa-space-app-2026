// Thin client for the EARTH SENSES API. Every number the UI shows comes from these calls.
/* eslint-disable @typescript-eslint/no-explicit-any */
export type Investigation = any
export type Comparison = any
export type Evidence = any

export interface Region { id: string; name: string; latitude: number; longitude: number; note: string; cached_periods: [number, number][] }
export interface Catalog {
  variables: Record<string, { label: string; definition: string; verified: boolean }>
  default_variables: string[]
  regions: Region[]
  first_year: number
  last_complete_year: number
  network_allowed: boolean
}
export interface InvestigateBody {
  latitude: number; longitude: number; start: number; end: number; variables: string[]
  region_name?: string; baseline_start?: number; baseline_end?: number
}

async function call<T>(path: string, body?: unknown): Promise<T> {
  const res = await fetch(path, body === undefined ? undefined : {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body),
  })
  if (!res.ok) {
    let detail = `${res.status} ${res.statusText}`
    try {
      const j = await res.json()
      detail = typeof j.detail === 'string' ? j.detail : JSON.stringify(j.detail)
    } catch { /* keep the status text */ }
    throw new Error(detail)
  }
  return res.json() as Promise<T>
}

export const api = {
  catalog: () => call<Catalog>('/api/catalog'),
  investigate: (b: InvestigateBody) => call<Investigation>('/api/investigate', b),
  report: (b: InvestigateBody) => call<{ markdown: string }>('/api/report', b),
  compare: (b: unknown) => call<Comparison>('/api/compare', b),
  guard: (text: string, claim_type: string) => call<any>('/api/guard/check', { text, claim_type }),
}
