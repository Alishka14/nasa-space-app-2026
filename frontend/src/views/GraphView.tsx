/* eslint-disable @typescript-eslint/no-explicit-any */
import { useState } from 'react'
import { api, type Investigation } from '../api'
import { chrome, fmt, seriesColor, type Mode } from '../theme'
import { Card, Status, Verdict, type T } from './common'

const W = 760
const H = 470
const DASH: Record<string, string> = { SUPPORTED: '', WEAK: '10 7', INCONCLUSIVE: '3 7', NOT_SUPPORTED: '1 9' }

/** Evidence-backed relationship graph. Geometry only encodes computed numbers:
 * width = |detrended r|, colour = sign, dash = status. */
export default function GraphView({ inv, t, mode, onEvidence }: {
  inv: Investigation; t: T; mode: Mode; onEvidence: (id: string) => void
}) {
  const c = chrome[mode]
  const nodes: any[] = inv.graph.nodes
  const edges: any[] = inv.graph.edges
  const [text, setText] = useState('Rising temperature causes relative humidity to fall, which proves the link.')
  const [verdict, setVerdict] = useState<any>(null)
  const pos: Record<string, [number, number]> = {}
  nodes.forEach((n, i) => {
    const a = -Math.PI / 2 + (2 * Math.PI * i) / nodes.length
    pos[n.id] = nodes.length === 1 ? [W / 2, H / 2] : [W / 2 + 250 * Math.cos(a), H / 2 + 34 + 140 * Math.sin(a)]
  })
  const statusOf = (id: string) => inv.evidence.find((e: any) => e.id === id)?.status ?? 'OBSERVED'

  return (
    <div className="stack">
      <Card title={t('tabGraph')} right={<span className="muted small">{inv.region.name} · {inv.request.start}–{inv.request.end}</span>}>
        <p className="hint">{t('graphRule')}</p>
        <svg viewBox={`0 0 ${W} ${H}`} className="graph" role="img" aria-label="Relationship graph">
          {edges.map(e => {
            const [x1, y1] = pos[e.source]
            const [x2, y2] = pos[e.target]
            const mx = (x1 + x2) / 2
            const my = (y1 + y2) / 2
            const col = e.r_detrended < 0 ? c.neg : c.pos
            return (
              <g key={e.id} className="edge" onClick={() => onEvidence(e.evidence_id)} tabIndex={0} role="button"
                 onKeyDown={ev => ev.key === 'Enter' && onEvidence(e.evidence_id)}>
                <line x1={x1} y1={y1} x2={x2} y2={y2} stroke="transparent" strokeWidth={26} />
                <line x1={x1} y1={y1} x2={x2} y2={y2} stroke={col} strokeWidth={2 + 12 * Math.abs(e.r_detrended)}
                      strokeDasharray={DASH[e.status]} strokeLinecap="round" opacity={e.status === 'NOT_SUPPORTED' ? 0.45 : 1} />
                <g transform={`translate(${mx},${my})`}>
                  <rect x={-74} y={-25} width={148} height={50} rx={8} fill={c.surface} stroke={c.axis} />
                  <text textAnchor="middle" y={-6} fill={c.ink} fontSize={14} fontWeight={700}>r = {fmt(e.r_detrended, 2)}</text>
                  <text textAnchor="middle" y={12} fill={c.ink2} fontSize={11}>{e.status}{e.hypothesis_id ? ' · ✎' : ''}{e.sign_differs_between_seasons ? ' · ▲ season' : ''}</text>
                </g>
              </g>
            )
          })}
          {nodes.map(n => {
            const [x, y] = pos[n.id]
            const up = y < H / 2          // label goes on the side facing away from the centre
            return (
              <g key={n.id} className="node" transform={`translate(${x},${y})`} onClick={() => onEvidence(n.evidence_id)} tabIndex={0} role="button"
                 onKeyDown={ev => ev.key === 'Enter' && onEvidence(n.evidence_id)}>
                <circle r={50} fill={c.surface} stroke={seriesColor(n.id, mode)} strokeWidth={5} />
                <text textAnchor="middle" y={-4} fill={c.ink} fontSize={n.id.length > 8 ? 10.5 : 13} fontWeight={700}>{n.id}</text>
                <text textAnchor="middle" y={14} fill={c.ink2} fontSize={11}>{fmt(n.slope, 3)}/yr</text>
                <text textAnchor="middle" y={up ? -78 : 70} fill={c.ink} fontSize={12}>{n.label}</text>
                <text textAnchor="middle" y={up ? -62 : 86} fill={c.muted} fontSize={11}>{n.trend_verdict.replaceAll('_', ' ').toLowerCase()}</text>
              </g>
            )
          })}
        </svg>
        <div className="legend">
          <span><i style={{ background: c.neg }} /> anomalies vary in opposite directions</span>
          <span><i style={{ background: c.pos }} /> anomalies vary in the same direction</span>
          <span>line width = |r| of detrended anomalies</span>
          <span>solid = supported · dashed = weak · dotted = inconclusive</span>
          <span>✎ = an untested hypothesis is attached · ▲ season = sign differs between seasons</span>
        </div>
      </Card>

      <div className="grid cards-3">
        {edges.map(e => (
          <Card key={e.id} title={`${e.source} ↔ ${e.target}`} right={<Status code={statusOf(e.evidence_id)} />}>
            <Verdict code={e.status} />
            <dl className="facts">
              <dt>raw r</dt><dd>{fmt(e.r_raw, 2)}</dd>
              <dt>deseasonalized</dt><dd>{fmt(e.r_deseasonalized, 2)}</dd>
              <dt>detrended</dt><dd>{fmt(e.r_detrended, 2)} ({fmt(e.ci95[0], 2)} to {fmt(e.ci95[1], 2)})</dd>
              <dt>lag scan</dt><dd>{e.lag_verdict.replaceAll('_', ' ').toLowerCase()}{e.significant_nonzero_lags.length ? `: ${e.significant_nonzero_lags.map((k: number) => (k > 0 ? '+' : '') + k).join(', ')}` : ''}</dd>
            </dl>
            <div className="actions">
              <button className="link" onClick={() => onEvidence(e.evidence_id)}>{t('viewEvidence')} →</button>
              {e.hypothesis_id && <button className="link" onClick={() => onEvidence(e.hypothesis_id)}>✎ Hypothesis →</button>}
            </div>
          </Card>
        ))}
      </div>

      <Card title={t('guardTitle')}>
        <p className="hint">{t('guardHint')}</p>
        <textarea value={text} onChange={e => setText(e.target.value)} rows={3} />
        <div className="actions">
          <button className="primary small" onClick={async () => setVerdict(await api.guard(text, 'statistical_relationship').catch(e => ({ error: String(e.message) })))}>{t('check')}</button>
        </div>
        {verdict && !verdict.error && (
          <div className={'guard ' + (verdict.allowed ? 'ok' : 'no')}>
            <strong>{verdict.allowed ? '✔ ' + t('allowed') : '✖ ' + t('blocked')}</strong>
            {verdict.violations.map((v: any) => <p key={v.rule}><code>{v.rule}</code> “{v.matches.join('”, “')}” — {v.message}</p>)}
            {verdict.notices.map((v: any) => <p key={v.rule} className="muted"><code>{v.rule}</code> {v.message}</p>)}
            {verdict.allowed && <p className="muted">Passing the guard means no known overclaim was found. It does not make the statement true.</p>}
          </div>
        )}
        {verdict?.error && <div className="banner error">{verdict.error}</div>}
      </Card>
    </div>
  )
}
