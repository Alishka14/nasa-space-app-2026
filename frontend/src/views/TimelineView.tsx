/* eslint-disable @typescript-eslint/no-explicit-any */
import type { Investigation } from '../api'
import { Card, type T } from './common'

/** EarthChangeEpisode: Observation → Hypothesis → Test → Counterexample → Revision → Conclusion. */
export default function TimelineView({ inv, t, onEvidence }: { inv: Investigation; t: T; onEvidence: (id: string) => void }) {
  return (
    <div className="stack">
      <Card title={t('tabTimeline')} right={<code title={inv.data_hash}>data {inv.data_hash.slice(0, 12)}…</code>}>
        <p className="hint">{t('timelineHint')}</p>
      </Card>
      {inv.episodes.map((ep: any) => (
        <Card key={ep.id} title={<>{ep.kind === 'trend' ? 'Trend' : 'Relationship'} · {ep.subject.join(' ↔ ')}</>}
              right={<span className="muted small">{ep.id} · {ep.period[0]}–{ep.period[1]}</span>}>
          <ol className="episode">
            {ep.steps.map((s: any) => (
              <li key={s.stage} className={'stage st-' + s.stage.toLowerCase()}>
                <span className="stage-name">{s.stage}</span>
                <p>{s.text}{s.reason && <em className="muted"> (reason: {s.reason})</em>}</p>
              </li>
            ))}
          </ol>
          <div className="actions">
            {ep.evidence_ids.map((id: string) => <button key={id} className="link" onClick={() => onEvidence(id)}>{id} →</button>)}
          </div>
        </Card>
      ))}
    </div>
  )
}
