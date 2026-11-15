// What the onboarding screens can ask of a globe. Implemented by the WebGL
// EarthScene and by the 2D fallback, so the screens do not care which one runs.

export interface EarthView {
  lat: number
  lon: number
  /** Camera distance in Earth radii (default 3.4). */
  dist?: number
  /** Horizontal shift of the globe in screen widths (-0.5 … 0.5), for layouts with text beside it. */
  x?: number
  /** Vertical shift of the globe in screen heights (-0.5 … 0.5); negative moves it down. */
  y?: number
  /** Degrees per second of slow spin after the move ends (0 = hold still). */
  spin?: number
}

export interface EarthOverlays {
  /** Opacity of the glowing Natural Earth coastlines, 0–1. */
  coast?: number
  /** Opacity of the 30° graticule, 0–1. */
  graticule?: number
  /** Opacity of the Pavlodar marker and its pulse, 0–1. */
  marker?: number
  /** 0 = natural colours, 1 = cool analytical tint. */
  tint?: number
}

export interface ScreenPoint { x: number; y: number; visible: boolean }

export interface EarthController {
  readonly kind: 'webgl' | '2d'
  setView(v: EarthView, seconds?: number): void
  setOverlays(o: EarthOverlays, seconds?: number): void
  setMarker(lat: number, lon: number): void
  /** Screen position of the marker in CSS pixels relative to the canvas. */
  markerScreen(): ScreenPoint | null
  /** Freeze the clock at t seconds (video capture); null returns to real time. */
  setManualTime(t: number | null): void
  dispose(): void
}

export interface EarthCallbacks {
  onProgress?: (fraction: number) => void
  onReady?: () => void
  reducedMotion?: boolean
}

export const PAVLODAR = { lat: 52.29, lon: 76.97 }
