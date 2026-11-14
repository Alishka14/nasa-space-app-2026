/* eslint-disable @typescript-eslint/no-explicit-any */
import { useState } from 'react'
import Chart from '../Chart'
import { api, type Catalog, type Comparison } from '../api'
import { compareSeries } from '../charts'
import type { Mode } from '../theme'
import { Card, Verdict, type T } from './common'

export default function CompareView({ catalog, start, end, vars, t, mode }: {
  catalog: Catalog; start: number; end: number; vars: string[]; t: T; mode: Mode
}) {
  const [a, setA] = useState(catalog.regions[0].id)
  const [b, setB] = useState(catalog.regions[1].id)
  const [res, setRes] = useState<Comparison | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const pick = (id: string) => catalog.regions.find(r => r.id === id)!

  const run = async () => {
    const ra = pick(a)
    const rb = pick(b)
    setBusy(true); setError(null)
    try {
      setRes(await api.compare({
        region_a: { name: ra.name, latitude: ra.latitude, longitude: ra.longitude },
        region_b: { name: rb.name, latitude: rb.latitude, longitude: rb.longitude }, start, end, variables: vars,
      }))
    } catch (e) { setError(e instanceof Error ? e.message : String(e)); setRes(null) } finally { setBusy(false) }
  }

  return (
    <div className="stack">
      <Card title={t('tabCompare')} right={<span className="muted small">{start}–{end} · {vars.join(', ')}</span>}>
        <p className="hint">The same variable can trend one way in one region and the other way elsewhere. Both places are analysed over the same years;
          the difference series shows whether they are drifting apart.</p>
        <div className="row three">
          <label>{t('regionA')}<select value={a} onChange={e => setA(e.target.value)}>
            {catalog.regions.map(r => <option key={r.id} value={r.id}>{r.name}{r.cached_periods.length ? '' : ' (live)'}</option>)}</select></label>
          <label>{t('regionB')}<select value={b} onChange={e => setB(e.target.value)}>
            {catalog.regions.map(r => <option key={r.id} value={r.id}>{r.name}{r.cached_periods.length ? '' : ' (live)'}</option>)}</select></label>
          <button className="primary" onClick={run} disabled={busy || a === b}>{busy ? t('working') : t('compareRun')}</button>
        </div>
        {error && <div className="banner error" role="alert">{error}</div>}
      </Card>
      {res && (
        <>
          <Card>
            <p className="muted">Grid-cell mean elevation: {res.region_a.name} {res.region_a.grid_cell_elevation_m} m · {res.region_b.name} {res.region_b.grid_cell_elevation_m} m.
              Levels differ with elevation; only the changes over time are compared.</p>
          </Card>
          {res.variables.map((v: any) => (
            <Card key={v.variable} title={`${v.label} (${v.units})`} right={<Verdict code={v.verdict} />}>
              <p className="statement">{v.statement}</p>
              <Chart option={compareSeries(v, res.region_a.name, res.region_b.name, mode)} height={300} />
            </Card>
          ))}
          <Card title={t('limitations')}><ul>{res.limitations.map((l: string) => <li key={l}>{l}</li>)}</ul></Card>
        </>
      )}
    </div>
  )
}
