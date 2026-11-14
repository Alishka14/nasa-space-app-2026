// 2D fallback for browsers without WebGL. It is NOT a 3D model: land from Natural
// Earth is sampled into dots and drawn with an orthographic projection on a 2D
// canvas, so the same camera moves still read as a rotating globe. The interface
// says which one is running (kind = '2d'), and the screens label it.
import { DEG, Tween, landPolygons, nearestAngle, seeded, yawFor } from './geo'
import { PAVLODAR, type EarthCallbacks, type EarthController, type EarthOverlays, type EarthView, type ScreenPoint } from './types'

const DEFAULT_DIST = 3.4

export class FlatGlobe implements EarthController {
  readonly kind = '2d' as const
  private ctx: CanvasRenderingContext2D
  private land: [number, number, number][] = []
  private stars: [number, number, number][] = []
  private markerLL = { ...PAVLODAR }
  private raf = 0
  private manual: number | null = null
  private readonly t0 = performance.now() / 1000
  private lat = new Tween(20 * DEG)
  private yaw = new Tween(yawFor(40))
  private spinSpeed = 4 * DEG
  private spinStart = 0
  private dist = new Tween(DEFAULT_DIST)
  private shiftX = new Tween(0)
  private shiftY = new Tween(0)
  private marker = new Tween(0)
  private coast = new Tween(0)
  private lastMarker: ScreenPoint | null = null

  constructor(private canvas: HTMLCanvasElement, private cb: EarthCallbacks = {}) {
    const ctx = canvas.getContext('2d')
    if (!ctx) throw new Error('2D canvas unavailable')
    this.ctx = ctx
    if (cb.reducedMotion) this.spinSpeed = 0
    this.land = sampleLand()
    const rand = seeded(7)
    for (let i = 0; i < 420; i++) this.stars.push([rand(), rand(), 0.2 + 0.8 * rand() ** 2])
    cb.onProgress?.(1)
    cb.onReady?.()
    this.loop = this.loop.bind(this)
    this.raf = requestAnimationFrame(this.loop)
  }

  setView(v: EarthView, seconds = 2.4): void {
    const now = this.now()
    const d = this.cb.reducedMotion ? Math.min(seconds, 0.4) : seconds
    const cur = this.currentYaw(now)
    this.yaw.jumpTo(cur)
    this.yaw.set(nearestAngle(cur, yawFor(v.lon)), d, now)
    this.lat.set(v.lat * DEG, d, now)
    this.dist.set(v.dist ?? DEFAULT_DIST, d, now)
    this.shiftX.set(v.x ?? 0, d, now)
    this.shiftY.set(v.y ?? 0, d, now)
    this.spinSpeed = this.cb.reducedMotion ? 0 : (v.spin ?? 0) * DEG
    this.spinStart = now + d
  }

  setOverlays(o: EarthOverlays, seconds = 1.2): void {
    const now = this.now()
    if (o.marker !== undefined) this.marker.set(o.marker, seconds, now)
    if (o.coast !== undefined) this.coast.set(o.coast, seconds, now)
  }

  setMarker(lat: number, lon: number): void { this.markerLL = { lat, lon } }
  markerScreen(): ScreenPoint | null { return this.lastMarker }
  setManualTime(t: number | null): void { this.manual = t; if (t !== null) this.draw() }
  dispose(): void { cancelAnimationFrame(this.raf) }

  private now(): number { return this.manual ?? performance.now() / 1000 - this.t0 }
  private currentYaw(now: number): number {
    return this.yaw.value(now) + this.spinSpeed * Math.max(0, now - this.spinStart)
  }
  private loop(): void {
    this.raf = requestAnimationFrame(this.loop)
    if (this.manual === null) this.draw()
  }

  private draw(): void {
    const dpr = Math.min(window.devicePixelRatio || 1, 2)
    const w = this.canvas.clientWidth
    const h = this.canvas.clientHeight
    if (this.canvas.width !== Math.round(w * dpr) || this.canvas.height !== Math.round(h * dpr)) {
      this.canvas.width = Math.round(w * dpr)
      this.canvas.height = Math.round(h * dpr)
    }
    const c = this.ctx
    c.setTransform(dpr, 0, 0, dpr, 0, 0)
    c.fillStyle = '#03050b'
    c.fillRect(0, 0, w, h)
    for (const [x, y, b] of this.stars) {
      c.fillStyle = `rgba(220,230,255,${b})`
      c.fillRect(x * w, y * h, 1.2, 1.2)
    }
    const now = this.now()
    const yaw = this.currentYaw(now)
    const tilt = this.lat.value(now)
    const dist = this.dist.value(now)
    const R = (Math.min(w, h) * 0.62) / (dist * Math.tan(16 * DEG))
    const cx = w / 2 + this.shiftX.value(now) * w
    const cy = h / 2 - this.shiftY.value(now) * h

    const glow = c.createRadialGradient(cx, cy, R * 0.92, cx, cy, R * 1.12)
    glow.addColorStop(0, 'rgba(70,140,255,0.35)')
    glow.addColorStop(1, 'rgba(70,140,255,0)')
    c.fillStyle = glow
    c.beginPath(); c.arc(cx, cy, R * 1.12, 0, Math.PI * 2); c.fill()
    const sea = c.createRadialGradient(cx - R * 0.3, cy - R * 0.3, R * 0.1, cx, cy, R)
    sea.addColorStop(0, '#12305a'); sea.addColorStop(1, '#050d1f')
    c.fillStyle = sea
    c.beginPath(); c.arc(cx, cy, R, 0, Math.PI * 2); c.fill()

    const cy0 = Math.cos(yaw), sy0 = Math.sin(yaw), ct = Math.cos(tilt), st = Math.sin(tilt)
    const rot = (x: number, y: number, z: number): [number, number, number] => {
      const x1 = x * cy0 + z * sy0, z1 = -x * sy0 + z * cy0
      return [x1, y * ct - z1 * st, y * st + z1 * ct]
    }
    const size = Math.max(1.2, R / 170)
    for (const [x, y, z] of this.land) {
      const [px, py, pz] = rot(x, y, z)
      if (pz <= 0) continue
      c.fillStyle = `rgba(127,214,255,${0.25 + 0.65 * pz})`
      c.fillRect(cx + px * R - size / 2, cy - py * R - size / 2, size, size)
    }
    const m = this.marker.value(now)
    const [mx, my, mz] = rot(...xyz(this.markerLL.lat, this.markerLL.lon))
    this.lastMarker = { x: cx + mx * R, y: cy - my * R, visible: mz > 0.15 }
    if (m > 0.01 && mz > 0) {
      const phase = (now % 2.4) / 2.4
      c.strokeStyle = `rgba(159,232,255,${m * (1 - phase)})`
      c.lineWidth = 1.5
      c.beginPath(); c.arc(this.lastMarker.x, this.lastMarker.y, 4 + phase * 16, 0, Math.PI * 2); c.stroke()
      c.fillStyle = `rgba(159,232,255,${m})`
      c.beginPath(); c.arc(this.lastMarker.x, this.lastMarker.y, 3.5, 0, Math.PI * 2); c.fill()
    }
  }
}

function xyz(lat: number, lon: number): [number, number, number] {
  const phi = (lon + 180) * DEG
  const theta = (90 - lat) * DEG
  return [-Math.cos(phi) * Math.sin(theta), Math.cos(theta), Math.sin(phi) * Math.sin(theta)]
}

/** Rasterise Natural Earth land into a small equirectangular mask and keep a dot every 1.5°. */
function sampleLand(): [number, number, number][] {
  const W = 480, H = 240
  const cv = document.createElement('canvas')
  cv.width = W; cv.height = H
  const c = cv.getContext('2d')
  if (!c) return []
  c.fillStyle = '#fff'
  for (const poly of landPolygons()) {
    c.beginPath()
    for (const ring of poly) {
      ring.forEach(([lon, lat], i) => {
        const x = ((lon + 180) / 360) * W
        const y = ((90 - lat) / 180) * H
        if (i === 0) c.moveTo(x, y); else c.lineTo(x, y)
      })
      c.closePath()
    }
    c.fill('evenodd')
  }
  const data = c.getImageData(0, 0, W, H).data
  const out: [number, number, number][] = []
  for (let lat = -84; lat <= 84; lat += 1.5) {
    const step = 1.5 / Math.max(0.2, Math.cos(lat * DEG))   // even spacing on the sphere
    for (let lon = -180; lon < 180; lon += step) {
      const x = Math.floor(((lon + 180) / 360) * W)
      const y = Math.floor(((90 - lat) / 180) * H)
      if (data[(y * W + x) * 4] > 127) out.push(xyz(lat, lon))
    }
  }
  return out
}
