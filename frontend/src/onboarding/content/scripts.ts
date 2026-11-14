import data from './intro-scripts.json'
import type { EarthOverlays, EarthView } from '../earth/types'
import type { UiLang } from '../i18n'
import type { VariantId } from '../storage'

export type Localized = Record<UiLang, string>
export type Visual = 'earth' | 'layers' | 'focus' | 'series-raw' | 'corr' | 'corr-flip' | 'title' | 'checks' | 'claims' | 'enter'

export interface Widget {
  type: 'series' | 'corr' | 'checks' | 'claims'
  mode?: 'raw' | 'anomaly'
  pair?: 'p_rh' | 't_rh'
  bars?: ('raw' | 'cycles' | 'deseason')[]
  flip?: boolean
}

export interface Scene {
  id: string
  dur: number
  visual: Visual
  camera?: EarthView
  overlays?: EarthOverlays
  widget?: Widget
  title: Localized
  vo: Localized
  guard: 'statistical' | 'meta'
  prompt: string
}

export interface Variant {
  id: VariantId
  file: string
  target: [number, number]
  audience: Localized
  concept: Localized
  tone: Localized
  scenes: Scene[]
}

export const VARIANTS = (data as unknown as { variants: Variant[] }).variants

export function getVariant(id: VariantId): Variant {
  return VARIANTS.find(v => v.id === id) ?? VARIANTS[0]
}

export function duration(v: Variant): number {
  return v.scenes.reduce((s, x) => s + x.dur, 0)
}

export interface Position { index: number; scene: Scene; start: number; local: number; progress: number }

export function positionAt(v: Variant, t: number): Position {
  let start = 0
  for (let i = 0; i < v.scenes.length; i++) {
    const s = v.scenes[i]
    if (t < start + s.dur || i === v.scenes.length - 1) {
      const local = Math.max(0, Math.min(s.dur, t - start))
      return { index: i, scene: s, start, local, progress: local / s.dur }
    }
    start += s.dur
  }
  throw new Error('variant has no scenes')
}
