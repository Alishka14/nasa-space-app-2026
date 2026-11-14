// A real WebGL Earth built with plain three.js: textured sphere with a day/night
// shader, atmospheric rim glow, Natural Earth coastlines and graticule as a data
// overlay, a pulsing marker for the investigated grid cell, and a seeded star field.
// Every animated value is a Tween evaluated against one clock, so a frame can be
// reproduced exactly (video capture sets the clock by hand).
import * as THREE from 'three'
// NASA images, byte-identical to the files in NASA's WorldWind repository; provenance and
// credits in textures/SOURCES.json (built by scripts/build_earth_textures.py).
import dayUrl from './textures/nasa-blue-marble-ng-200405-2048x1024.jpg'
import nightUrl from './textures/nasa-earth-at-night-2012-2048x1024.png'
import waterUrl from './textures/water-mask-natural-earth-50m.png'
import { atmosphereFragment, atmosphereVertex, globeFragment, globeVertex } from './shaders'
import { DEG, Tween, coastlines, latLonToXYZ, nearestAngle, seeded, yawFor } from './geo'
import { PAVLODAR, type EarthCallbacks, type EarthController, type EarthOverlays, type EarthView, type ScreenPoint } from './types'

const SUN = new THREE.Vector3(-0.82, 0.30, 0.48).normalize()
const DEFAULT_DIST = 3.4

export class EarthScene implements EarthController {
  readonly kind = 'webgl' as const
  private renderer: THREE.WebGLRenderer
  private scene = new THREE.Scene()
  private camera = new THREE.PerspectiveCamera(32, 1, 0.1, 200)
  private root = new THREE.Group()
  private tilt = new THREE.Group()
  private spin = new THREE.Group()
  private markerGroup = new THREE.Group()
  private globeMat: THREE.ShaderMaterial
  private coastMat: THREE.LineBasicMaterial
  private gratMat: THREE.LineBasicMaterial
  private markerMats: THREE.Material[] = []
  private pulse: THREE.Mesh
  private disposables: { dispose(): void }[] = []
  private raf = 0
  private manual: number | null = null
  private readonly t0 = performance.now() / 1000
  private reduced: boolean

  private lat = new Tween(20)
  private yaw = new Tween(yawFor(40))
  private yawOffset = 0
  private spinSpeed = 4 * DEG
  private spinStart = 0
  private dist = new Tween(DEFAULT_DIST)
  private shiftX = new Tween(0)
  private shiftY = new Tween(0)
  private coast = new Tween(0)
  private grat = new Tween(0)
  private marker = new Tween(0)
  private tint = new Tween(0)
  private ready = new Tween(0)
  private observer: ResizeObserver

  constructor(private canvas: HTMLCanvasElement, private cb: EarthCallbacks = {}) {
    this.reduced = !!cb.reducedMotion
    this.renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: false, powerPreference: 'high-performance' })
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2))
    this.renderer.setClearColor(0x03050b, 1)
    this.renderer.outputColorSpace = THREE.SRGBColorSpace
    if (this.reduced) this.spinSpeed = 0

    this.scene.add(this.stars())
    this.scene.add(this.root)
    this.root.add(this.tilt)
    this.tilt.add(this.spin)

    // --- globe -------------------------------------------------------------
    const placeholder = new THREE.DataTexture(new Uint8Array([4, 9, 20, 255]), 1, 1)
    placeholder.needsUpdate = true
    this.globeMat = new THREE.ShaderMaterial({
      vertexShader: globeVertex, fragmentShader: globeFragment,
      uniforms: {
        dayMap: { value: placeholder }, nightMap: { value: placeholder }, waterMap: { value: placeholder },
        sunDir: { value: SUN }, ready: { value: 0 }, dataTint: { value: 0 },
      },
    })
    const globeGeo = new THREE.SphereGeometry(1, 128, 96)
    this.spin.add(new THREE.Mesh(globeGeo, this.globeMat))
    this.disposables.push(globeGeo, this.globeMat, placeholder)

    // --- atmosphere (does not rotate; its lighting follows the fixed sun) -----
    const atmoGeo = new THREE.SphereGeometry(1.075, 96, 64)
    const atmoMat = new THREE.ShaderMaterial({
      vertexShader: atmosphereVertex, fragmentShader: atmosphereFragment,
      uniforms: { sunDir: { value: SUN }, glow: { value: new THREE.Color(0.32, 0.62, 1.0) }, strength: { value: 1.25 } },
      side: THREE.BackSide, blending: THREE.AdditiveBlending, transparent: true, depthWrite: false,
    })
    this.root.add(new THREE.Mesh(atmoGeo, atmoMat))
    this.disposables.push(atmoGeo, atmoMat)

    // --- data overlays ------------------------------------------------------
    this.coastMat = new THREE.LineBasicMaterial({ color: 0x7fd6ff, transparent: true, opacity: 0,
                                                   blending: THREE.AdditiveBlending, depthWrite: false })
    this.gratMat = new THREE.LineBasicMaterial({ color: 0x3d7ab8, transparent: true, opacity: 0,
                                                  blending: THREE.AdditiveBlending, depthWrite: false })
    this.spin.add(this.lines(coastlines(), 1.0025, this.coastMat))
    this.spin.add(this.lines(graticule(), 1.0015, this.gratMat))

    // --- marker for the investigated grid cell ------------------------------
    this.pulse = this.buildMarker()
    this.spin.add(this.markerGroup)
    this.setMarker(PAVLODAR.lat, PAVLODAR.lon)

    this.loadTextures()
    this.observer = new ResizeObserver(() => this.resize())
    this.observer.observe(canvas.parentElement ?? canvas)
    this.resize()
    this.loop = this.loop.bind(this)
    this.raf = requestAnimationFrame(this.loop)
  }

  // ---------------------------------------------------------------- public API
  setView(v: EarthView, seconds = 2.4): void {
    const now = this.now()
    const d = this.reduced ? Math.min(seconds, 0.4) : seconds
    const cur = this.currentYaw(now)
    this.yaw.jumpTo(cur)
    this.yawOffset = 0
    this.yaw.set(nearestAngle(cur, yawFor(v.lon)), d, now)
    this.lat.set(v.lat * DEG, d, now)
    this.dist.set(v.dist ?? DEFAULT_DIST, d, now)
    this.shiftX.set(v.x ?? 0, d, now)
    this.shiftY.set(v.y ?? 0, d, now)
    this.spinSpeed = this.reduced ? 0 : (v.spin ?? 0) * DEG
    this.spinStart = now + d
  }

  setOverlays(o: EarthOverlays, seconds = 1.2): void {
    const now = this.now()
    const d = this.reduced ? Math.min(seconds, 0.3) : seconds
    if (o.coast !== undefined) this.coast.set(o.coast, d, now)
    if (o.graticule !== undefined) this.grat.set(o.graticule, d, now)
    if (o.marker !== undefined) this.marker.set(o.marker, d, now)
    if (o.tint !== undefined) this.tint.set(o.tint, d, now)
  }

  setMarker(lat: number, lon: number): void {
    const n = new THREE.Vector3(...latLonToXYZ(lat, lon, 1))
    this.markerGroup.position.copy(n).multiplyScalar(1.003)   // just above the surface, no z-fighting
    this.markerGroup.quaternion.setFromUnitVectors(new THREE.Vector3(0, 0, 1), n)   // local frame, parents may rotate
  }

  markerScreen(): ScreenPoint | null {
    const world = new THREE.Vector3()
    this.markerGroup.getWorldPosition(world)
    const normal = world.clone().sub(this.root.getWorldPosition(new THREE.Vector3())).normalize()
    const toCam = this.camera.position.clone().sub(world).normalize()
    const p = world.clone().project(this.camera)
    const w = this.canvas.clientWidth
    const h = this.canvas.clientHeight
    return { x: (p.x + 1) / 2 * w, y: (1 - p.y) / 2 * h, visible: normal.dot(toCam) > 0.15 }
  }

  setManualTime(t: number | null): void {
    this.manual = t
    if (t !== null) this.renderFrame()
  }

  dispose(): void {
    cancelAnimationFrame(this.raf)
    this.observer.disconnect()
    for (const d of this.disposables) d.dispose()
    for (const m of this.markerMats) m.dispose()
    this.coastMat.dispose()
    this.gratMat.dispose()
    this.renderer.dispose()
  }

  // ---------------------------------------------------------------- internals
  private now(): number { return this.manual ?? performance.now() / 1000 - this.t0 }
  /** Wall-clock seconds: texture arrival is a real-world event, not part of the scripted timeline. */
  private realNow(): number { return performance.now() / 1000 - this.t0 }

  private currentYaw(now: number): number {
    return this.yaw.value(now) + this.yawOffset + this.spinSpeed * Math.max(0, now - this.spinStart)
  }

  private loop(): void {
    this.raf = requestAnimationFrame(this.loop)
    if (this.manual === null) this.renderFrame()
  }

  private renderFrame(): void {
    const now = this.now()
    this.spin.rotation.y = this.currentYaw(now)
    this.tilt.rotation.x = this.lat.value(now)
    const dist = this.dist.value(now)
    this.camera.position.set(0, 0, dist)
    this.camera.lookAt(0, 0, 0)
    // shift in screen widths -> world units at the globe's depth
    const halfWidth = Math.tan((this.camera.fov * DEG) / 2) * dist * this.camera.aspect
    this.root.position.x = this.shiftX.value(now) * 2 * halfWidth
    this.root.position.y = this.shiftY.value(now) * 2 * (halfWidth / this.camera.aspect)

    this.globeMat.uniforms.ready.value = this.ready.value(this.realNow())
    this.globeMat.uniforms.dataTint.value = this.tint.value(now)
    this.coastMat.opacity = 0.75 * this.coast.value(now)
    this.gratMat.opacity = 0.35 * this.grat.value(now)
    const m = this.marker.value(now)
    this.markerGroup.visible = m > 0.01
    const phase = this.reduced ? 0.35 : (now % 2.4) / 2.4
    this.pulse.scale.setScalar(1 + phase * 2.6)
    ;(this.pulse.material as THREE.MeshBasicMaterial).opacity = m * (1 - phase) * 0.8
    for (const mat of this.markerMats) if (mat !== this.pulse.material) mat.opacity = m

    this.renderer.render(this.scene, this.camera)
  }

  private resize(): void {
    const el = this.canvas.parentElement ?? this.canvas
    const w = Math.max(1, el.clientWidth)
    const h = Math.max(1, el.clientHeight)
    this.renderer.setSize(w, h, false)
    this.camera.aspect = w / h
    this.camera.updateProjectionMatrix()
    if (this.manual !== null) this.renderFrame()
  }

  private loadTextures(): void {
    const manager = new THREE.LoadingManager()
    manager.onProgress = (_u, loaded, total) => this.cb.onProgress?.(loaded / total)
    manager.onLoad = () => {
      this.ready.set(1, this.reduced ? 0.2 : 1.4, this.realNow())
      this.cb.onReady?.()
    }
    manager.onError = () => {
      // Keep the placeholder sphere, overlays and atmosphere; say so through onReady as well.
      this.cb.onReady?.()
    }
    const loader = new THREE.TextureLoader(manager)
    const aniso = Math.min(8, this.renderer.capabilities.getMaxAnisotropy())
    const take = (url: string, uniform: string, srgb: boolean) => loader.load(url, tex => {
      tex.colorSpace = srgb ? THREE.SRGBColorSpace : THREE.NoColorSpace
      tex.anisotropy = aniso
      this.globeMat.uniforms[uniform].value = tex
      this.disposables.push(tex)
    })
    take(dayUrl, 'dayMap', true)
    take(nightUrl, 'nightMap', true)
    take(waterUrl, 'waterMap', false)
  }

  private lines(polylines: number[][][], r: number, mat: THREE.LineBasicMaterial): THREE.LineSegments {
    const pts: number[] = []
    for (const line of polylines) {
      for (let i = 1; i < line.length; i++) {
        const [lon0, lat0] = line[i - 1]
        const [lon1, lat1] = line[i]
        if (Math.abs(lon1 - lon0) > 180) continue // do not draw across the antimeridian
        pts.push(...latLonToXYZ(lat0, lon0, r), ...latLonToXYZ(lat1, lon1, r))
      }
    }
    const geo = new THREE.BufferGeometry()
    geo.setAttribute('position', new THREE.Float32BufferAttribute(pts, 3))
    this.disposables.push(geo)
    return new THREE.LineSegments(geo, mat)
  }

  private buildMarker(): THREE.Mesh {
    const add = (geo: THREE.BufferGeometry, mat: THREE.Material) => {
      this.disposables.push(geo)
      this.markerMats.push(mat)
      const mesh = new THREE.Mesh(geo, mat)
      this.markerGroup.add(mesh)
      return mesh
    }
    const glow = () => new THREE.MeshBasicMaterial({ color: 0x9fe8ff, transparent: true, opacity: 0,
                                                       blending: THREE.AdditiveBlending, depthWrite: false, side: THREE.DoubleSide })
    add(new THREE.CircleGeometry(0.0075, 32), glow())
    add(new THREE.RingGeometry(0.0125, 0.0145, 48), glow())
    const pulse = add(new THREE.RingGeometry(0.011, 0.0135, 48), glow())
    // a short beam pointing out of the surface
    const beamGeo = new THREE.CylinderGeometry(0.0016, 0.0016, 0.22, 8)
    beamGeo.rotateX(Math.PI / 2)
    beamGeo.translate(0, 0, 0.11)
    add(beamGeo, glow())
    return pulse
  }

  private stars(): THREE.Group {
    const group = new THREE.Group()
    const rand = seeded(20261114)
    const layer = (count: number, size: number, minB: number) => {
      const pos: number[] = []
      const col: number[] = []
      for (let i = 0; i < count; i++) {
        const u = rand() * 2 - 1
        const a = rand() * Math.PI * 2
        const s = Math.sqrt(1 - u * u)
        pos.push(60 * s * Math.cos(a), 60 * u, 60 * s * Math.sin(a))
        const b = minB + (1 - minB) * Math.pow(rand(), 2.2)
        const warm = rand() * 0.18
        col.push(b * (0.86 + warm), b * 0.92, b * (1.04 - warm))
      }
      const geo = new THREE.BufferGeometry()
      geo.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3))
      geo.setAttribute('color', new THREE.Float32BufferAttribute(col, 3))
      const mat = new THREE.PointsMaterial({ size, sizeAttenuation: false, vertexColors: true, transparent: true,
                                             depthWrite: false })
      this.disposables.push(geo, mat)
      group.add(new THREE.Points(geo, mat))
    }
    layer(2400, 1.3, 0.18)
    layer(140, 2.4, 0.55)
    return group
  }
}

function graticule(): number[][][] {
  const out: number[][][] = []
  for (let lon = -180; lon < 180; lon += 30) {
    const line: number[][] = []
    for (let lat = -80; lat <= 80; lat += 2) line.push([lon, lat])
    out.push(line)
  }
  for (let lat = -60; lat <= 60; lat += 30) {
    const line: number[][] = []
    for (let lon = -180; lon <= 180; lon += 2) line.push([lon, lat])
    out.push(line)
  }
  return out
}
