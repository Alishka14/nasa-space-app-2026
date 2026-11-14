// Chart tokens. Categorical colours follow the entity, never its rank; the three
// leading slots were checked for colour-vision-deficiency separation in both modes.
export type Mode = 'light' | 'dark'

export const chrome = {
  light: { surface: '#fcfcfb', ink: '#0b0b0b', ink2: '#52514e', muted: '#898781', grid: '#e1e0d9', axis: '#c3c2b7',
           neg: '#2a78d6', pos: '#e34948', mid: '#f0efec' },
  dark: { surface: '#1a1a19', ink: '#f0efec', ink2: '#c3c2b7', muted: '#898781', grid: '#2c2c2a', axis: '#383835',
          neg: '#3987e5', pos: '#e66767', mid: '#383835' },
} as const

const SERIES: Record<string, { light: string; dark: string }> = {
  PRECTOTCORR: { light: '#2a78d6', dark: '#3987e5' },
  T2M: { light: '#eb6834', dark: '#d95926' },
  RH2M: { light: '#1baf7a', dark: '#199e70' },
  WS2M: { light: '#eda100', dark: '#c98500' },
  T2M_MIN: { light: '#e87ba4', dark: '#d55181' },
  GWETTOP: { light: '#008300', dark: '#0ca30c' },
  QV2M: { light: '#6250d6', dark: '#9085e9' },
  T2M_MAX: { light: '#e34948', dark: '#e66767' },
}

export function seriesColor(variable: string, mode: Mode): string {
  return (SERIES[variable] ?? { light: '#898781', dark: '#898781' })[mode]
}

export const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

export function fmt(x: number | null | undefined, nd = 3, sign = true): string {
  if (x === null || x === undefined || !Number.isFinite(x)) return 'n/a'
  const s = x.toFixed(nd)
  return sign && x > 0 ? `+${s}` : s
}
export function fmtP(p: number | null | undefined): string {
  if (p === null || p === undefined) return 'n/a'
  return p < 0.001 ? '< 0.001' : p.toFixed(3)
}
