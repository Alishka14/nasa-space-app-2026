// Geometry shared by the WebGL globe and the 2D fallback.
// Mapping follows three.js SphereGeometry with an equirectangular texture:
// longitude 0 at the texture centre, longitude -180 at its left edge.
import { feature, mesh } from 'topojson-client'
import world from 'world-atlas/countries-110m.json'
import type { Topology, GeometryCollection } from 'topojson-specification'

export const DEG = Math.PI / 180

export interface LatLon { lat: number; lon: number }

/** Unit-sphere position of a latitude/longitude, matching SphereGeometry UVs. */
export function latLonToXYZ(lat: number, lon: number, r = 1): [number, number, number] {
  const phi = (lon + 180) * DEG
  const theta = (90 - lat) * DEG
  return [-r * Math.cos(phi) * Math.sin(theta), r * Math.cos(theta), r * Math.sin(phi) * Math.sin(theta)]
}

/** Spin about the polar axis that brings a longitude to face the camera (+z). */
export function yawFor(lon: number): number {
  const phi = (lon + 180) * DEG
  return -Math.atan2(-Math.cos(phi), Math.sin(phi))
}

/** Shortest-path target for an angle, so a camera move never spins the long way round. */
export function nearestAngle(current: number, target: number): number {
  const tau = Math.PI * 2
  let d = (target - current) % tau
  if (d > Math.PI) d -= tau
  if (d < -Math.PI) d += tau
  return current + d
}

const topo = world as unknown as Topology<{ countries: GeometryCollection; land: GeometryCollection }>

/** Coastlines from Natural Earth 1:110m (public domain) as polylines of [lon, lat]. */
export function coastlines(): number[][][] {
  const m = mesh(topo, topo.objects.land)
  return m.coordinates as number[][][]
}

/** Land polygons (for rasterising a land mask in the 2D fallback). */
export function landPolygons(): number[][][][] {
  const f = feature(topo, topo.objects.land) as unknown as GeoJSON.FeatureCollection | GeoJSON.Feature
  const geoms = 'features' in f ? f.features.map(x => x.geometry) : [f.geometry]
  const out: number[][][][] = []
  for (const g of geoms) {
    if (g.type === 'Polygon') out.push(g.coordinates as number[][][])
    else if (g.type === 'MultiPolygon') out.push(...(g.coordinates as number[][][][]))
  }
  return out
}

export const easeInOutCubic = (k: number) => (k < 0.5 ? 4 * k * k * k : 1 - Math.pow(-2 * k + 2, 3) / 2)
export const clamp01 = (k: number) => Math.min(1, Math.max(0, k))

/** A value that moves to a target over a duration, evaluated against an explicit clock. */
export class Tween {
  private from: number
  private to: number
  private t0 = 0
  private dur = 0
  constructor(v: number) { this.from = v; this.to = v }
  value(now: number): number {
    if (this.dur <= 0) return this.to
    const k = clamp01((now - this.t0) / this.dur)
    return this.from + (this.to - this.from) * easeInOutCubic(k)
  }
  target(): number { return this.to }
  end(): number { return this.t0 + this.dur }
  jumpTo(v: number): void { this.from = v; this.to = v; this.dur = 0 }
  set(to: number, dur: number, now: number): void {
    this.from = this.value(now)
    this.to = to
    this.t0 = now
    this.dur = Math.max(0, dur)
  }
  done(now: number): boolean { return this.dur <= 0 || now - this.t0 >= this.dur }
}

/** Deterministic pseudo-random numbers (mulberry32), so the star field is identical on every run. */
export function seeded(seed: number): () => number {
  let a = seed >>> 0
  return () => {
    a |= 0; a = (a + 0x6d2b79f5) | 0
    let t = Math.imul(a ^ (a >>> 15), 1 | a)
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }
}
