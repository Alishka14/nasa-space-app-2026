import { useEffect, useRef, useState } from 'react'
import { EarthScene } from './EarthScene'
import { FlatGlobe } from './FlatGlobe'
import type { EarthController } from './types'

interface Props {
  onController: (c: EarthController) => void
  onProgress?: (fraction: number) => void
  onReady?: () => void
  reducedMotion?: boolean
  /** Shown in the corner when the 2D fallback is used. */
  fallbackLabel: string
}

function webglAvailable(): boolean {
  if (new URLSearchParams(window.location.search).get('earth') === '2d') return false
  try {
    const c = document.createElement('canvas')
    return !!(c.getContext('webgl2') || c.getContext('webgl'))
  } catch {
    return false
  }
}

/** Full-bleed globe. Creates the WebGL Earth, or the labelled 2D fallback when WebGL is unavailable. */
export default function EarthCanvas({ onController, onProgress, onReady, reducedMotion, fallbackLabel }: Props) {
  const ref = useRef<HTMLCanvasElement>(null)
  const [kind, setKind] = useState<'webgl' | '2d' | null>(null)
  const cbs = useRef({ onController, onProgress, onReady })
  cbs.current = { onController, onProgress, onReady }

  useEffect(() => {
    const canvas = ref.current
    if (!canvas) return
    const callbacks = {
      reducedMotion,
      onProgress: (f: number) => cbs.current.onProgress?.(f),
      onReady: () => cbs.current.onReady?.(),
    }
    let ctl: EarthController
    if (webglAvailable()) {
      try {
        ctl = new EarthScene(canvas, callbacks)
      } catch {
        ctl = new FlatGlobe(replaceCanvas(canvas), callbacks)
      }
    } else {
      ctl = new FlatGlobe(canvas, callbacks)
    }
    setKind(ctl.kind)
    cbs.current.onController(ctl)
    return () => ctl.dispose()
  }, [reducedMotion])

  return (
    <div className="es-earth" data-earth={kind ?? 'loading'}>
      <canvas ref={ref} aria-hidden="true" />
      {kind === '2d' && <div className="es-earth-note">{fallbackLabel}</div>}
    </div>
  )
}

/** A canvas that already tried WebGL cannot give a 2D context; swap in a fresh one. */
function replaceCanvas(old: HTMLCanvasElement): HTMLCanvasElement {
  const fresh = document.createElement('canvas')
  fresh.setAttribute('aria-hidden', 'true')
  old.replaceWith(fresh)
  return fresh
}
