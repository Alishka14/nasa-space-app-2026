import { useEffect, useRef } from 'react'
import maplibregl from 'maplibre-gl'
import { feature, mesh } from 'topojson-client'
import world from 'world-atlas/countries-110m.json'
import type { Region } from './api'
import type { Mode } from './theme'

// The basemap is drawn from Natural Earth outlines bundled with the app, so the map
// works without any tile server. The rectangle is the MERRA-2 grid cell that a
// "point" request actually returns.
const COLORS = {
  light: { sea: '#dfe9f2', land: '#f4f3ee', border: '#b9b8b0', cell: '#0b0b0b' },
  dark: { sea: '#10161d', land: '#26282b', border: '#4a4c50', cell: '#f0efec' },
}

/* eslint-disable @typescript-eslint/no-explicit-any */
const topo = world as any
const LAND = feature(topo, topo.objects.land) as any
const BORDERS = mesh(topo, topo.objects.countries, (a: any, b: any) => a !== b) as any

/** MERRA-2 cell (0.5 x 0.625 degrees) enclosing a point. */
export function merraCell(lat: number, lon: number) {
  const clat = Math.round(lat / 0.5) * 0.5
  const clon = Math.round(lon / 0.625) * 0.625
  const [s, n, w, e] = [clat - 0.25, clat + 0.25, clon - 0.3125, clon + 0.3125]
  return { type: 'Feature' as const, properties: {},
           geometry: { type: 'Polygon' as const, coordinates: [[[w, s], [e, s], [e, n], [w, n], [w, s]]] } }
}

export default function MapPanel({ regions, lat, lon, mode, onPick, onRegion }: {
  regions: Region[]; lat: number; lon: number; mode: Mode
  onPick: (lat: number, lon: number) => void; onRegion: (r: Region) => void
}) {
  const el = useRef<HTMLDivElement>(null)
  const map = useRef<maplibregl.Map | null>(null)
  const markers = useRef<maplibregl.Marker[]>([])
  const point = useRef<maplibregl.Marker | null>(null)
  const handlers = useRef({ onPick, onRegion })
  handlers.current = { onPick, onRegion }

  useEffect(() => {
    if (!el.current) return
    const c = COLORS[mode]
    const m = new maplibregl.Map({
      container: el.current, center: [72, 47], zoom: 2.4, attributionControl: false,
      style: {
        version: 8, projection: { type: 'globe' },
        sources: { land: { type: 'geojson', data: LAND }, borders: { type: 'geojson', data: BORDERS },
                   cell: { type: 'geojson', data: merraCell(lat, lon) } },
        layers: [
          { id: 'sea', type: 'background', paint: { 'background-color': c.sea } },
          { id: 'land', type: 'fill', source: 'land', paint: { 'fill-color': c.land } },
          { id: 'borders', type: 'line', source: 'borders', paint: { 'line-color': c.border, 'line-width': 0.7 } },
          { id: 'cell', type: 'line', source: 'cell', paint: { 'line-color': c.cell, 'line-width': 1.5 } },
        ],
      } as any,
    })
    m.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'top-right')
    m.addControl(new maplibregl.AttributionControl({ compact: true, customAttribution: 'Outlines: Natural Earth' }))
    m.on('click', e => handlers.current.onPick(Number(e.lngLat.lat.toFixed(2)), Number(e.lngLat.lng.toFixed(2))))
    map.current = m
    return () => { m.remove(); map.current = null }
    // the map is created once; later changes are applied by the effects below
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => {
    const m = map.current
    if (!m) return
    const apply = () => {
      const c = COLORS[mode]
      m.setPaintProperty('sea', 'background-color', c.sea)
      m.setPaintProperty('land', 'fill-color', c.land)
      m.setPaintProperty('borders', 'line-color', c.border)
      m.setPaintProperty('cell', 'line-color', c.cell)
    }
    if (m.isStyleLoaded()) apply(); else m.once('load', apply)
  }, [mode])

  useEffect(() => {
    const m = map.current
    if (!m) return
    markers.current.forEach(k => k.remove())
    markers.current = regions.map(r => {
      const node = document.createElement('button')
      const active = Math.abs(r.latitude - lat) < 1e-9 && Math.abs(r.longitude - lon) < 1e-9
      node.className = 'map-marker' + (active ? ' active' : '') + (r.cached_periods.length ? '' : ' live')
      node.textContent = r.name.split(',')[0]
      node.title = r.note
      node.addEventListener('click', ev => { ev.stopPropagation(); handlers.current.onRegion(r) })
      return new maplibregl.Marker({ element: node, anchor: 'bottom' }).setLngLat([r.longitude, r.latitude]).addTo(m)
    })
    point.current?.remove()
    const dot = document.createElement('div')
    dot.className = 'map-point'
    point.current = new maplibregl.Marker({ element: dot }).setLngLat([lon, lat]).addTo(m)
    const setCell = () => (m.getSource('cell') as maplibregl.GeoJSONSource | undefined)?.setData(merraCell(lat, lon))
    if (m.isStyleLoaded()) setCell(); else m.once('load', setCell)
    m.easeTo({ center: [lon, lat], zoom: Math.max(m.getZoom(), 3.2), duration: 600 })
  }, [regions, lat, lon])

  return <div ref={el} className="map" aria-label="World map for choosing a location" />
}
