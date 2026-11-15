import type { ReactNode } from 'react'
import type { tr } from '../i18n'
import { replicatedLabel, statusLabel, verdictLabel } from '../sciI18n'

export type T = ReturnType<typeof tr>

// Status is never colour alone: every badge carries an icon and a label.
const VERDICTS: Record<string, { icon: string; label: string; tone: string }> = {
  ROBUST_TREND: { icon: '✔', label: 'Robust trend', tone: 'good' },
  FRAGILE_TREND: { icon: '▲', label: 'Fragile — not established', tone: 'warn' },
  NO_SIGNIFICANT_TREND_DETECTED: { icon: '○', label: 'No significant trend detected', tone: 'neutral' },
  SUPPORTED: { icon: '✔', label: 'Supported association', tone: 'good' },
  WEAK: { icon: '≈', label: 'Weak association', tone: 'neutral' },
  INCONCLUSIVE: { icon: '?', label: 'Inconclusive', tone: 'warn' },
  NOT_SUPPORTED: { icon: '○', label: 'Not supported', tone: 'neutral' },
  LAGGED_ASSOCIATION_DETECTED: { icon: '✔', label: 'Lagged association detected', tone: 'good' },
  NO_LAGGED_ASSOCIATION_DETECTED: { icon: '○', label: 'No lagged association detected', tone: 'neutral' },
  UNTESTED: { icon: '✎', label: 'Untested', tone: 'hyp' },
  CHECKS_PASSED: { icon: '✔', label: 'Data checks passed', tone: 'good' },
  OPPOSITE_SIGNIFICANT_TRENDS: { icon: '⇄', label: 'Opposite significant trends', tone: 'good' },
  REGIONS_DIVERGE: { icon: '⇄', label: 'Regions diverge', tone: 'good' },
  OPPOSITE_SIGNS_NOT_SIGNIFICANT: { icon: '?', label: 'Opposite signs, not significant', tone: 'warn' },
  NO_SIGNIFICANT_DIFFERENCE_DETECTED: { icon: '○', label: 'No significant difference detected', tone: 'neutral' },
  DERIVED_VARIABLE_CONFIRMED: { icon: '⚙', label: 'Computed from the other variables', tone: 'warn' },
  DERIVED_VARIABLE_CHECK_INCONCLUSIVE: { icon: '?', label: 'Derived-variable check inconclusive', tone: 'warn' },
}

export function Verdict({ code }: { code: string | null | undefined }) {
  const v = VERDICTS[code ?? ''] ?? { icon: '·', label: code ?? 'n/a', tone: 'neutral' }
  return <span className={`badge ${v.tone}`}><span aria-hidden="true">{v.icon}</span> {verdictLabel(code ?? '', v.label)}</span>
}

const STATUS_HELP: Record<string, string> = {
  HYPOTHESIS: 'Proposed, not tested here',
  OBSERVED: 'Computed from real data by this engine',
}
export function Status({ code }: { code: string }) {
  return <span className={`status s-${code.toLowerCase()}`} title={STATUS_HELP[code] ?? code}>{statusLabel(code)}</span>
}

/** Record status plus, where independent reports agree, how many of its numbers were replicated. */
export function EvidenceStatus({ ev }: { ev: { status: string; replicated_values?: string[] } | undefined }) {
  if (!ev) return null
  const n = ev.replicated_values?.length ?? 0
  return (
    <>
      <Status code={ev.status} />
      {n > 0 && <span className="status s-replicated" title="These numbers were also reported independently and agree. The record as a whole stays OBSERVED.">
        {replicatedLabel(n)}</span>}
    </>
  )
}

export function Card({ title, right, children, className }: { title?: ReactNode; right?: ReactNode; children: ReactNode; className?: string }) {
  return (
    <section className={'panel card ' + (className ?? '')}>
      {(title || right) && <header className="card-head"><h3>{title}</h3><div className="card-right">{right}</div></header>}
      {children}
    </section>
  )
}

export function Swatch({ color }: { color: string }) {
  return <span className="swatch" style={{ background: color }} aria-hidden="true" />
}
