/* eslint-disable @typescript-eslint/no-explicit-any */
import { useEffect } from 'react'
import type { Investigation } from '../api'
import { EvidenceStatus, Verdict, type T } from './common'

/** View Evidence: the claim, the NASA data behind it, the method, the result,
 * what speaks against it, what else could explain it, and what it cannot show. */
export default function EvidenceDrawer({ inv, id, t, onClose, onOpen }: {
  inv: Investigation; id: string; t: T; onClose: () => void; onOpen: (id: string) => void
}) {
  const ev = inv.evidence.find((e: any) => e.id === id)
  useEffect(() => {
    const h = (e: KeyboardEvent) => e.key === 'Escape' && onClose()
    window.addEventListener('keydown', h)
    return () => window.removeEventListener('keydown', h)
  }, [onClose])
  if (!ev) return null
  const hyp = inv.evidence.find((e: any) => e.claim_type === 'unverified_physical_explanation' && e.parameters.attached_to === ev.id)
  const months: string[] = inv.series.months
  const vars: string[] = ev.variables.filter((v: string) => inv.series.raw[v])
  const isHyp = ev.status === 'HYPOTHESIS'

  return (
    <div className="drawer-backdrop" onClick={onClose}>
      <aside className="drawer" role="dialog" aria-modal="true" aria-label="Evidence record" onClick={e => e.stopPropagation()}>
        <header>
          <div><code>{ev.id}</code> <EvidenceStatus ev={ev} /> <Verdict code={ev.verdict} /></div>
          <button onClick={onClose} aria-label={t('close')}>✕</button>
        </header>

        {isHyp && <div className="hypothesis"><strong>✎ {t('hypothesis')}</strong></div>}
        <h4>{t('claim')}</h4>
        <p className="claim">{ev.claim}</p>
        <p className="muted small">{ev.claim_type.replaceAll('_', ' ')} · {ev.region.name} · {ev.period[0]}–{ev.period[1]} · {ev.variables.join(', ')}</p>

        {ev.supporting_evidence.length > 0 && <><h4>{t('evidenceFor')}</h4><ul>{ev.supporting_evidence.map((s: string) => <li key={s}>{s}</li>)}</ul></>}
        {ev.counterevidence.length > 0 && <><h4>{t('counter')}</h4><ul className="counter">{ev.counterevidence.map((s: string) => <li key={s}>{s}</li>)}</ul></>}
        {ev.alternatives.length > 0 && <><h4>{t('alternatives')}</h4><ul>{ev.alternatives.map((s: string) => <li key={s}>{s}</li>)}</ul></>}
        {hyp && (
          <div className="hypothesis">
            <strong>✎ {t('hypothesis')}</strong><p>{hyp.claim}</p>
            <button className="link" onClick={() => onOpen(hyp.id)}>{hyp.id} →</button>
          </div>
        )}
        {ev.independent_reports.length > 0 && (
          <>
            <h4>{t('independent')}</h4>
            <div className="table-wrap"><table>
              <thead><tr><th>Metric</th><th>Reported</th><th>Ours</th><th>|diff|</th><th></th></tr></thead>
              <tbody>{ev.independent_reports.map((m: any) => (
                <tr key={m.metric}><td><code>{m.metric}</code></td><td>{m.reported}</td><td>{m.ours.toFixed(4)}</td><td>{m.abs_diff.toFixed(4)}</td>
                  <td>{m.agrees ? '✔ replicated' : '✖ differs'}</td></tr>))}</tbody>
            </table></div>
            <p className="muted small">{ev.independent_reports[0].source}. {ev.independent_reports[0].independence}.</p>
          </>
        )}

        <h4>{t('method')}</h4>
        <p>{ev.method}</p>
        <h4>{t('parameters')}</h4>
        <pre className="json">{JSON.stringify(ev.parameters, null, 1)}</pre>
        {!isHyp && <><h4>{t('result')}</h4><pre className="json">{JSON.stringify(ev.result, null, 1)}</pre>
          <h4>{t('uncertainty')}</h4><pre className="json">{JSON.stringify(ev.uncertainty, null, 1)}</pre></>}
        <h4>{t('limitations')}</h4>
        <ul>{ev.limitations.map((s: string) => <li key={s}>{s}</li>)}</ul>

        <h4>{t('sourceData')}</h4>
        {inv.provenance.map((p: any) => (
          <dl className="facts wide" key={p.sha256}>
            <dt>Source</dt><dd>{p.original_source}</dd>
            <dt>Request</dt><dd><code className="wrap">{p.original_api_request}</code></dd>
            <dt>Retrieved</dt><dd>{p.retrieval_timestamp}</dd>
            <dt>Raw file</dt><dd><code className="wrap">data/{p.raw_path}</code></dd>
            <dt>SHA-256</dt><dd><code className="wrap">{p.sha256}</code></dd>
          </dl>
        ))}
        <p className="muted small">Data hash of this analysis: <code className="wrap">{ev.data_hash}</code></p>
        {vars.length > 0 && (
          <div className="table-wrap tall"><table>
            <thead><tr><th>Month</th>{vars.map(v => <th key={v}>{v} ({inv.variables[v].display_units})</th>)}</tr></thead>
            <tbody>{months.map((m, i) => <tr key={m}><td>{m}</td>{vars.map(v => <td key={v}>{inv.series.raw[v][i]}</td>)}</tr>)}</tbody>
          </table></div>
        )}
      </aside>
    </div>
  )
}
