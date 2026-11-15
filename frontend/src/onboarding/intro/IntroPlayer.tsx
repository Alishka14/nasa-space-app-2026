// Plays one intro variant over the shared globe. Time is a single number t
// (seconds); scenes, text fades, widgets and the globe's camera all derive from
// it. Real playback advances t with requestAnimationFrame; capture mode
// (?capture) exposes window.__esIntro.seek(t) so frames can be rendered exactly.
import { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } from 'react'
import { IntroAudio, soundPreferred } from './introAudio'
import { duration, positionAt, type Variant } from '../content/scripts'
import { fill, makeT, type UiLang } from '../i18n'
import type { EarthController, ScreenPoint } from '../earth/types'
import { LayerChips, PlaceLabel, WidgetView, fadeInOut, ramp } from './widgets'

interface Props {
  variant: Variant
  lang: UiLang
  earth: EarthController | null
  capture: boolean
  onFinish: () => void
  onSkip: () => void
}

declare global {
  interface Window {
    __esIntro?: { seek: (t: number) => void; duration: number; ready: boolean; boundaries: (t: number) => number[] }
  }
}

export default function IntroPlayer({ variant, lang, earth, capture, onFinish, onSkip }: Props) {
  const t = useMemo(() => makeT(lang), [lang])
  const total = duration(variant)
  const [time, setTime] = useState(0)
  const [playing, setPlaying] = useState(!capture)
  const [subs, setSubs] = useState(true)
  const [marker, setMarker] = useState<ScreenPoint | null>(null)
  const [sound, setSound] = useState(soundPreferred())
  const audio = useRef<IntroAudio | null>(null)
  if (!capture && !audio.current) audio.current = new IntroAudio(sound)
  const appliedScene = useRef<string | null>(null)
  const finished = useRef(false)
  const pos = positionAt(variant, time)
  const sceneId = variant.scenes[pos.index].id
  // Sound: one voice line per scene, music bed underneath; follows play/pause; silent in capture mode.
  useEffect(() => { if (playing) audio.current?.scene(sceneId, lang) }, [sceneId]) // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => { if (playing) audio.current?.resume(); else audio.current?.pause() }, [playing])
  useEffect(() => () => audio.current?.stop(), [])

  // Apply camera and overlays when a new scene starts.
  const applyScene = useCallback((index: number) => {
    const scene = variant.scenes[index]
    if (!earth || appliedScene.current === scene.id) return
    appliedScene.current = scene.id
    // A captured film opens on its first framing; live playback glides there from the previous screen.
    const move = capture && index === 0 ? 0 : Math.min(2.4, scene.dur * 0.45)
    if (scene.camera) earth.setView(scene.camera, move)
    if (scene.overlays) earth.setOverlays(scene.overlays, Math.min(1.4, scene.dur * 0.3))
  }, [earth, variant, capture])

  useEffect(() => { if (!capture) applyScene(pos.index) }, [pos.index, applyScene, capture])

  // Real-time playback.
  useEffect(() => {
    if (capture || !playing) return
    let raf = 0
    let last = performance.now()
    const tick = (now: number) => {
      const dt = Math.min(0.25, (now - last) / 1000)   // slow frames still keep real time; a long stall does not jump
      last = now
      setTime(x => Math.min(total, x + dt))
      if (earth) setMarker(earth.markerScreen())
      raf = requestAnimationFrame(tick)
    }
    raf = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(raf)
  }, [playing, capture, total, earth])

  useEffect(() => {
    if (time >= total && !finished.current && !capture) {
      finished.current = true
      onFinish()
    }
  }, [time, total, onFinish, capture])

  // Capture mode: deterministic seeking.
  useEffect(() => {
    if (!capture || !earth) return
    window.__esIntro = {
      duration: total,
      ready: true,
      // start times of the scene before t and of the scene containing t
      boundaries: (s: number) => {
        const p = positionAt(variant, s)
        const prev = p.index > 0 ? p.start - variant.scenes[p.index - 1].dur : 0
        return p.index > 0 ? [prev, p.start] : [0]
      },
      seek: (s: number) => {
        earth.setManualTime(s)
        applyScene(positionAt(variant, s).index)
        earth.setManualTime(s)
        setMarker(earth.markerScreen())
        setTime(s)
      },
    }
    return () => { delete window.__esIntro }
  }, [capture, earth, total, variant, applyScene])

  const replay = useCallback(() => {
    audio.current?.stop()
    appliedScene.current = null
    finished.current = false
    setTime(0)
    setPlaying(true)
  }, [])

  useEffect(() => {
    if (capture) return
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') { e.preventDefault(); onSkip() }
      else if (e.key === ' ') { e.preventDefault(); setPlaying(p => !p) }
      else if (e.key.toLowerCase() === 'r') replay()
      else if (e.key.toLowerCase() === 'c') setSubs(s => !s)
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [capture, onSkip, replay])

  const s = pos.scene
  const textAlpha = fadeInOut(pos.local, s.dur)
  const title = fill(s.title[lang], lang)
  const vo = fill(s.vo[lang], lang)
  const layout = s.widget ? 'with-panel' : `solo-${s.visual}`

  // A long title can wrap onto an extra line; push the panel down so the two never touch.
  const titleRef = useRef<HTMLHeadingElement>(null)
  const panelRef = useRef<HTMLDivElement>(null)
  useLayoutEffect(() => {
    const place = () => {
      const h = titleRef.current, p = panelRef.current
      if (!h || !p) return
      p.style.top = ''
      const needed = h.offsetTop + h.offsetHeight + 14
      if (p.offsetTop < needed) p.style.top = `${needed}px`
    }
    place()
    window.addEventListener('resize', place)
    return () => window.removeEventListener('resize', place)
  }, [s.id, title])

  return (
    <div className={`es-intro es-layout-${layout}`} data-scene={s.id} data-capture={capture ? '1' : undefined}>
      {s.visual === 'focus' && <PlaceLabel marker={marker} p={pos.progress} t={t} />}
      {s.visual === 'layers' && <LayerChips marker={marker} p={pos.progress} t={t} />}

      <div className="es-stage">
        <h2 ref={titleRef} className={`es-title es-title-${s.visual}${title === 'EARTH SENSES' ? ' es-title-wordmark' : ''}`} style={{ opacity: textAlpha, transform: `translateY(${(1 - ramp(pos.local / s.dur, 0, 0.12)) * 10}px)` }}>
          {title}
        </h2>
        {s.widget && (
          <div ref={panelRef} className="es-panel" style={{ opacity: Math.min(1, pos.local / 0.5, (s.dur - pos.local) / 0.35) }}>
            <WidgetView widget={s.widget} p={pos.progress} lang={lang} t={t} />
          </div>
        )}
        {s.visual === 'enter' && !capture && (
          <button className="es-enter" onClick={onFinish} style={{ opacity: ramp(pos.progress, 0.25, 0.5) }}>{t('common.openApp')} →</button>
        )}
      </div>

      {subs && <p className="es-subtitle" style={{ opacity: textAlpha }} lang={lang}>{vo}</p>}

      {capture && <div className="es-capture-source">{t('intro.source')}</div>}
      {!capture && (
        <div className="es-controls">
          <div className="es-progress" aria-hidden="true">
            {variant.scenes.map((x, i) => {
              const fillW = i < pos.index ? 1 : i === pos.index ? pos.progress : 0
              return <span key={x.id} style={{ flex: x.dur }}><i style={{ width: `${fillW * 100}%` }} /></span>
            })}
          </div>
          <div className="es-buttons">
            <button onClick={() => setPlaying(p => !p)} aria-label={playing ? t('intro.pause') : t('intro.play')}>{playing ? '❚❚' : '▶'} <span>{playing ? t('intro.pause') : t('intro.play')}</span></button>
            <button onClick={replay}>↺ <span>{t('intro.replay')}</span></button>
            <button onClick={() => setSubs(x => !x)} aria-pressed={subs}>CC <span>{t('intro.subtitles')}</span></button>
            <span className="es-time">{fmtTime(time)} / {fmtTime(total)}</span>
            <button onClick={() => { const v = !sound; setSound(v); audio.current?.setOn(v); if (v && playing) audio.current?.scene(sceneId, lang) }} aria-pressed={sound}>{sound ? '🔊' : '🔇'} <span>{t('intro.sound')}</span></button>
            <button className="es-skip" onClick={onSkip}>{t('intro.skip')} · Esc</button>
          </div>
          <div className="es-source">{t('intro.source')}</div>
        </div>
      )}
    </div>
  )
}

function fmtTime(s: number): string {
  const v = Math.floor(s)
  return `${Math.floor(v / 60)}:${String(v % 60).padStart(2, '0')}`
}
