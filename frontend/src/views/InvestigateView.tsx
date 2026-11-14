/* eslint-disable @typescript-eslint/no-explicit-any */
import { useMemo, useState } from 'react'
import Chart from '../Chart'
import { annualHeight, annualTrends, climatology, correlationSteps, lagScan, seasonSplit, stackedHeight, stackedSeries, windowHeatmap } from '../charts'
import type { Investigation } from '../api'
import { fmt, fmtP, seriesColor, type Mode } from '../theme'
import { Card, Status, Swatch, Verdict, type T } from './common'

type SeriesTab = 'raw' | 'cycle' | 'anomalies' | 'annual'

export default function InvestigateView({ inv, t, mode, onEvidence }: {
  inv: Investigation; t: T; mode: Mode; onEvidence: (id: string) => void
}) {
  const vars: string[] = inv.request.variables
  const infos = inv.variables
  const [seriesTab, setSeriesTab] = useState<SeriesTab>('annual')
  const [table, setTable] = useState(false)
  const [winVar, setWinVar] = useState(vars[0])
  const wv = vars.includes(winVar) ? winVar : vars[0]
  const statusOf = (id: string) => inv.evidence.find((e: any) => e.id === id)?.status ?? 'OBSERVED'

  const seriesOption = useMemo(() => {
    if (seriesTab === 'raw') return stackedSeries(inv.series.months, vars, inv.series.raw, infos, mode, { monthly: true })
    if (seriesTab === 'anomalies') return stackedSeries(inv.series.months, vars, inv.series.anomaly, infos, mode, { monthly: true, zero: true })
    if (seriesTab === 'cycle') return climatology(vars, inv.series.climatology, infos, mode)
    return annualTrends(vars, inv.trends, infos, mode)
  }, [seriesTab, inv, mode, vars, infos])
  const p0 = inv.provenance[0]

  return (
    <div className="stack">
      <Card>
        <div className="summary">
          <div>
            <h2>{inv.region.name}</h2>
            <p className="muted">
              {inv.region.latitude}, {inv.region.longitude} · grid cell mean elevation {inv.region.grid_cell_elevation_m} m ·{' '}
              {inv.request.start}–{inv.request.end} · baseline {inv.request.baseline[0]}–{inv.request.baseline[1]}
            </p>
          </div>
          <div className="summary-right">
            <span className="chip ok">NASA POWER · MERRA-2 · {inv.data_source}</span>
            <code title={inv.data_hash}>data {inv.data_hash.slice(0, 12)}…</code>
          </div>
        </div>
        {inv.warnings.length > 0 && <ul className="warnings">{inv.warnings.map((w: string) => <li key={w}>▲ {w}</li>)}</ul>}
        {t('engineEnglish') && <p className="hint">{t('engineEnglish')}</p>}
      </Card>

      <h2 className="section">{t('changing')}</h2>
      <div className="grid cards-3">
        {vars.map(v => {
          const tr_ = inv.trends[v]
          const s = tr_.summary
          return (
            <Card key={v} title={<><Swatch color={seriesColor(v, mode)} />{infos[v].label}</>} right={<Status code={statusOf(tr_.evidence_id)} />}>
              <p className="definition">{infos[v].definition}</p>
              <div className="big">{fmt(s.primary_slope)} <small>{tr_.slope_units}</small></div>
              <dl className="facts">
                <dt>95% CI</dt><dd>{fmt(s.primary_ci[0])} to {fmt(s.primary_ci[1])}</dd>
                <dt>p (adjusted)</dt><dd>{fmtP(s.primary_p)}</dd>
                <dt>q (FDR)</dt><dd>{fmtP(tr_.q)}</dd>
                <dt>per decade</dt><dd>{fmt(tr_.per_decade, 2)} {infos[v].display_units}</dd>
              </dl>
              <Verdict code={tr_.verdict} />
              <p className="statement">{tr_.statement}</p>
              {tr_.annual_total && (
                <p className="muted small">Annual total: mean {tr_.annual_total.mean.toFixed(0)} mm/year; slope{' '}
                  {fmt(tr_.annual_total.summary.primary_slope, 2)} {tr_.annual_total.slope_units} (p = {fmtP(tr_.annual_total.summary.primary_p)}).</p>
              )}
              <button className="link" onClick={() => onEvidence(tr_.evidence_id)}>{t('viewEvidence')} →</button>
            </Card>
          )
        })}
      </div>

      <Card title={t('series')} right={
        <div className="seg">
          {([['annual', t('annual')], ['raw', t('raw')], ['cycle', t('cycle')], ['anomalies', t('anomalies')]] as [SeriesTab, string][]).map(([id, label]) => (
            <button key={id} className={seriesTab === id ? 'on' : ''} onClick={() => setSeriesTab(id)}>{label}</button>
          ))}
          <button className={table ? 'on' : ''} onClick={() => setTable(!table)}>{t('table')}</button>
        </div>}>
        {seriesTab === 'annual' && <p className="hint">Coloured: annual means for the analysed period. Dashed: Theil–Sen line. Grey: the longer record, where available.</p>}
        {seriesTab === 'anomalies' && <p className="hint">Each value minus the {inv.request.baseline[0]}–{inv.request.baseline[1]} mean of its calendar month.</p>}
        <Chart option={seriesOption} height={seriesTab === 'annual' ? annualHeight(vars.length) : stackedHeight(vars.length)} />
        {table && (
          <div className="table-wrap">
            <table>
              <thead><tr><th>Year</th>{vars.map(v => <th key={v}>{infos[v].label} ({infos[v].display_units})</th>)}</tr></thead>
              <tbody>{inv.trends[vars[0]].annual.years.map((y: number, i: number) => (
                <tr key={y}><td>{y}</td>{vars.map(v => <td key={v}>{inv.trends[v].annual.values[i].toFixed(2)}</td>)}</tr>))}</tbody>
            </table>
          </div>
        )}
      </Card>

      <Card title={t('windowTitle')} right={
        <div className="seg">{vars.map(v => <button key={v} className={wv === v ? 'on' : ''} onClick={() => setWinVar(v)}>{v}</button>)}</div>}>
        <p className="hint">{t('windowHint')} {inv.trends[wv].window_sensitivity.n_windows} sub-periods of at least {inv.trends[wv].window_sensitivity.min_len} years:
          slope positive in {inv.trends[wv].window_sensitivity.n_positive}, negative in {inv.trends[wv].window_sensitivity.n_negative},
          individually significant in {inv.trends[wv].window_sensitivity.n_significant}.</p>
        <Chart option={windowHeatmap(inv.trends[wv], mode)} height={280} />
      </Card>

      {inv.relationships.length > 0 && <h2 className="section">{t('together')}</h2>}
      {inv.relationships.map((r: any) => {
        const hyp = r.hypothesis_id ? inv.evidence.find((e: any) => e.id === r.hypothesis_id) : null
        return (
          <Card key={r.id} title={<>{infos[r.x].label} ↔ {infos[r.y].label}</>}
                right={<><Verdict code={r.status} /> <Status code={statusOf(r.evidence_id)} /></>}>
            <p className="statement">{r.statement}</p>
            <div className="grid charts-3">
              <figure><figcaption>{t('stepsTitle')}</figcaption><Chart option={correlationSteps(r, mode)} height={170} /></figure>
              <figure><figcaption>{t('seasonTitle')}{r.by_season.sign_differs_between_seasons && <span className="badge warn"> ▲ sign differs</span>}</figcaption>
                <Chart option={seasonSplit(r, mode)} height={170} /></figure>
              <figure><figcaption>{t('lagTitle')} <Verdict code={r.lag_verdict} /></figcaption><Chart option={lagScan(r, mode)} height={170} /></figure>
            </div>
            <p className="hint">{t('lagHint')}</p>
            {hyp && <div className="hypothesis"><strong>✎ {t('hypothesis')}</strong><p>{hyp.claim}</p></div>}
            <div className="actions">
              <button className="link" onClick={() => onEvidence(r.evidence_id)}>{t('viewEvidence')} →</button>
              <button className="link" onClick={() => onEvidence(r.lag_evidence_id)}>Lag evidence →</button>
            </div>
          </Card>
        )
      })}

      <Card title={t('cannot')} className="cannot">
        <ul>{inv.cannot_conclude.map((c: string) => <li key={c}>{c}</li>)}</ul>
      </Card>

      <Card title={t('provenance')}>
        {inv.provenance.map((p: any) => (
          <dl className="facts wide" key={p.sha256}>
            <dt>Source</dt><dd>{p.original_source}</dd>
            <dt>Request</dt><dd><code className="wrap">{p.original_api_request}</code></dd>
            <dt>Retrieved</dt><dd>{p.retrieval_timestamp} — {p.retrieval_method}</dd>
            <dt>Coverage</dt><dd>{p.coverage.start} to {p.coverage.end}, {p.coverage.n_months} months</dd>
            <dt>SHA-256</dt><dd><code className="wrap">{p.sha256}</code></dd>
            <dt>Validation</dt><dd>{p.validation_status}</dd>
          </dl>
        ))}
        <p className="muted small">{p0.spatial_resolution}. Kind of data: {Object.values<any>(p0.variables)[0].kind}.</p>
      </Card>
    </div>
  )
}
