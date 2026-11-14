// Scene graphics for the intro. Every visual property is a function of the
// scene's progress p (0–1), never of wall-clock CSS animations, so a frame can
// be rendered at any exact time (video capture) and pausing freezes everything.
import series from '../content/series.json'
import { factText, factValue, formatNumber, type T, type UiLang } from '../i18n'
import type { Widget } from '../content/scripts'
import type { ScreenPoint } from '../earth/types'

export const COLORS = { PRECTOTCORR: '#3987e5', RH2M: '#199e70', T2M: '#d95926', neg: '#3987e5', pos: '#e66767' }

const ease = (k: number) => (k < 0.5 ? 4 * k * k * k : 1 - Math.pow(-2 * k + 2, 3) / 2)
export const ramp = (p: number, a: number, b: number) => ease(Math.min(1, Math.max(0, (p - a) / (b - a))))

/** Opacity for text that fades in at the start of a scene and out at its end. */
export function fadeInOut(local: number, dur: number, fin = 0.6, fout = 0.45): number {
  return Math.min(1, Math.max(0, local / fin), Math.max(0, (dur - local) / fout))
}

interface Props { widget: Widget; p: number; lang: UiLang; t: T }

export function WidgetView({ widget, p, lang, t }: Props) {
  if (widget.type === 'series') return <SeriesWidget mode={widget.mode ?? 'raw'} p={p} lang={lang} t={t} />
  if (widget.type === 'corr') return <CorrWidget widget={widget} p={p} lang={lang} t={t} />
  if (widget.type === 'checks') return <ChecksWidget p={p} t={t} />
  return <ClaimsWidget p={p} t={t} />
}

// ------------------------------------------------------------------ series
type SeriesData = { months: string[]; PRECTOTCORR: { raw: number[]; anomaly: number[] }; RH2M: { raw: number[]; anomaly: number[] } }
const S = series as unknown as SeriesData

function linePath(values: number[], w: number, h: number, mode: 'raw' | 'anomaly'): string {
  let lo: number, hi: number
  if (mode === 'raw') {
    lo = Math.min(...values); hi = Math.max(...values)
  } else {
    const sd = Math.sqrt(values.reduce((s, v) => s + v * v, 0) / values.length)
    lo = -3 * sd; hi = 3 * sd
  }
  const n = values.length
  return values.map((v, i) => {
    const x = (i / (n - 1)) * w
    const y = h - ((Math.min(hi, Math.max(lo, v)) - lo) / (hi - lo)) * h
    return `${i === 0 ? 'M' : 'L'}${x.toFixed(1)},${y.toFixed(1)}`
  }).join('')
}

function SeriesWidget({ mode, p, lang, t }: { mode: 'raw' | 'anomaly'; p: number; lang: UiLang; t: T }) {
  const W = 560, H = 190
  const draw = ramp(p, 0.04, 0.62)
  const showR = ramp(p, 0.62, 0.74)
  const years = [2001, 2006, 2011, 2016, 2021]
  const key = mode === 'raw' ? 'p_rh_raw' : 'p_rh_deseason'
  return (
    <div className="es-widget es-series">
      <div className="es-legend">
        <span><i style={{ background: COLORS.PRECTOTCORR }} />{t('var.PRECTOTCORR')}</span>
        <span><i style={{ background: COLORS.RH2M }} />{t('var.RH2M')}</span>
      </div>
      <svg viewBox={`0 -8 ${W} ${H + 30}`} role="img" aria-label={t(mode === 'raw' ? 'series.raw' : 'series.anomaly')}>
        {mode === 'anomaly' && <line x1={0} x2={W} y1={H / 2} y2={H / 2} className="es-axis" />}
        {years.map(y => {
          const x = ((y - 2001) * 12 / (S.months.length - 1)) * W
          return <g key={y}><line x1={x} x2={x} y1={0} y2={H} className="es-grid" /><text x={x + 3} y={H + 18} className="es-tick">{y}</text></g>
        })}
        {(['PRECTOTCORR', 'RH2M'] as const).map(v => (
          <path key={v} d={linePath(S[v][mode], W, H, mode)} pathLength={1} strokeDasharray="1"
                strokeDashoffset={1 - draw} fill="none" stroke={COLORS[v]} strokeWidth={1.6} strokeLinejoin="round" />
        ))}
      </svg>
      <div className="es-caption">{t(mode === 'raw' ? 'series.raw' : 'series.anomaly')} · {t('series.scaled')}</div>
      <div className="es-rvalue" style={{ opacity: showR }}>r = {factText(key, lang)}</div>
    </div>
  )
}

// ------------------------------------------------------------------ correlation bars
const BAR_FACT: Record<string, string> = { raw: 'raw', cycles: 'cycles', deseason: 'deseason' }
const BAR_LABEL = { raw: 'corr.raw', cycles: 'corr.cycles', deseason: 'corr.deseason' } as const

function CorrWidget({ widget, p, lang, t }: Props) {
  const pair = widget.pair ?? 'p_rh'
  const bars = widget.bars ?? ['raw', 'deseason']
  const rawValue = factValue(`${pair}_raw`)
  return (
    <div className="es-widget es-corr">
      <div className="es-widget-title">{t(pair === 'p_rh' ? 'corr.pair.p_rh' : 'corr.pair.t_rh')}</div>
      <div className="es-scale"><span>−1</span><span>0</span><span>+1</span></div>
      {bars.map((b, i) => {
        const target = factValue(`${pair}_${BAR_FACT[b]}`)
        const startAt = 0.06 + i * (widget.flip ? 0.2 : 0.22)
        const appear = ramp(p, startAt, startAt + 0.1)
        let v: number
        let settledAt: number
        if (widget.flip && b === 'deseason') {
          settledAt = startAt + 0.42
          v = rawValue + (target - rawValue) * ramp(p, startAt + 0.06, settledAt)
        } else {
          settledAt = startAt + 0.22
          v = target * ramp(p, startAt, settledAt)
        }
        // Only the bar moves. The printed number is always the engine's value and appears once the bar has
        // settled, so a paused frame or a screenshot never shows an in-between number next to a label.
        const valueOpacity = ramp(p, settledAt - 0.04, settledAt)
        const w = Math.abs(v) * 50
        const colour = v < 0 ? COLORS.neg : COLORS.pos
        return (
          <div key={b} className="es-bar-row" style={{ opacity: appear }}>
            <div className="es-bar-label">{t(BAR_LABEL[b])}</div>
            <div className="es-bar-track">
              <div className="es-bar-zero" />
              <div className="es-bar" style={{ left: `${v < 0 ? 50 - w : 50}%`, width: `${w}%`, background: colour }} />
            </div>
            <div className="es-bar-value" style={{ color: 'var(--es-ink)', opacity: valueOpacity }}>{formatNumber(target, 3, true, lang)}</div>
          </div>
        )
      })}
      {pair === 't_rh' && <div className="es-note" style={{ opacity: ramp(p, 0.55, 0.65) }}>⚙ {t('corr.builtIn')}</div>}
    </div>
  )
}

// ------------------------------------------------------------------ checks
const CHECKS = ['checks.seasons', 'checks.tests', 'checks.periods', 'checks.winter', 'checks.causation', 'checks.scope'] as const

function ChecksWidget({ p, t }: { p: number; t: T }) {
  return (
    <div className="es-widget es-checks">
      <div className="es-widget-title">{t('checks.title')}</div>
      <ul>
        {CHECKS.map((k, i) => {
          const a = ramp(p, 0.06 + i * 0.11, 0.14 + i * 0.11)
          return (
            <li key={k} style={{ opacity: a, transform: `translateX(${(1 - a) * 14}px)` }}>
              <span className="es-tick-mark" aria-hidden="true">{k === 'checks.causation' ? '≠' : k === 'checks.scope' ? '◎' : '✓'}</span>
              {t(k)}
            </li>
          )
        })}
      </ul>
    </div>
  )
}

// ------------------------------------------------------------------ rejected claims
function ClaimsWidget({ p, t }: { p: number; t: T }) {
  const items = [['claims.warming', 'claims.warmingWhy'], ['claims.humidity', 'claims.humidityWhy']] as const
  return (
    <div className="es-widget es-claims">
      <div className="es-widget-title">{t('claims.title')}</div>
      {items.map(([claim, why], i) => {
        const a = ramp(p, 0.06 + i * 0.3, 0.16 + i * 0.3)
        const strike = ramp(p, 0.14 + i * 0.3, 0.26 + i * 0.3)
        return (
          <div key={claim} className="es-claim" style={{ opacity: a }}>
            <div className="es-claim-text">
              <span className="es-claim-quote">{t(claim)}<i style={{ width: `${strike * 100}%` }} /></span>
              <span className="es-claim-tag" style={{ opacity: strike }}>{t('claims.rejected')}</span>
            </div>
            <div className="es-claim-why">{t(why)}</div>
          </div>
        )
      })}
    </div>
  )
}

// ------------------------------------------------------------------ labels pinned to the globe
export function PlaceLabel({ marker, p, t }: { marker: ScreenPoint | null; p: number; t: T }) {
  if (!marker || !marker.visible) return null
  const a = ramp(p, 0.25, 0.45)
  return (
    <div className="es-place" style={{ left: marker.x, top: marker.y, opacity: a }}>
      <svg width="140" height="60" className="es-leader" aria-hidden="true"><path d="M0,60 L40,8 L140,8" /></svg>
      <div className="es-place-text"><b>{t('place.pavlodar')}</b><small>{t('place.cell')}</small></div>
    </div>
  )
}

export function LayerChips({ marker, p, t }: { marker: ScreenPoint | null; p: number; t: T }) {
  const anchor = marker && marker.visible ? marker : null
  const vars = ['T2M', 'RH2M', 'PRECTOTCORR'] as const
  // A short readout stacked to the right of the marker, like an instrument callout.
  return (
    <>
      {vars.map((v, i) => {
        const a = ramp(p, 0.2 + i * 0.12, 0.34 + i * 0.12)
        const style = anchor
          ? { left: anchor.x + 44, top: anchor.y - 62 + i * 46, opacity: a, transform: `translateX(${(1 - a) * 12}px)` }
          : { right: '8%', top: `${30 + i * 9}%`, opacity: a }
        return (
          <div key={v} className="es-chip" data-i={i} style={style}>
            <i style={{ background: COLORS[v] }} />{t(`var.${v}`)} <code>{v}</code>
          </div>
        )
      })}
    </>
  )
}
