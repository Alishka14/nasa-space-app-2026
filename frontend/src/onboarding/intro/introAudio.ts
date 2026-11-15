// Sound for the live intro: a quiet music bed plus one synthetic voice-over line per scene
// (the same ElevenLabs lines as the films, labelled "AI voice" in the player). Starts only after the
// user has started the intro (browser autoplay rules) and never in capture mode. A line that runs past
// its scene finishes; the next scene's line waits for it, and a stale waiting line is dropped.
const FILM: Record<string, string> = { h: 'hero', e: 'explainer', t: 'teaser' }
const BASE = import.meta.env.BASE_URL || '/'
const KEY = 'es.sound'
// Lines that could not be generated (ElevenLabs credits ran out): those scenes stay music-only.
const MISSING = new Set(['explainer_kk/e3', 'explainer_kk/e5', 'explainer_kk/e7', 'teaser_kk/t2', 'teaser_kk/t4'])

export function soundPreferred(): boolean {
  try { return localStorage.getItem(KEY) !== 'off' } catch { return true }
}
export function rememberSound(on: boolean): void {
  try { localStorage.setItem(KEY, on ? 'on' : 'off') } catch { /* private mode: keep in memory only */ }
}

export class IntroAudio {
  private music = new Audio(`${BASE}audio/music_bed.mp3`)
  private voice: HTMLAudioElement | null = null
  private pending: string | null = null
  private on: boolean
  private active = false

  constructor(on: boolean) {
    this.on = on
    this.music.loop = true
    this.music.volume = 0.16
  }

  private url(sceneId: string, lang: string): string | null {
    const film = FILM[sceneId.charAt(0)]
    if (!film || MISSING.has(`${film}_${lang}/${sceneId}`)) return null
    return `${BASE}audio/${film}_${lang}/${sceneId}.mp3`
  }

  private playVoice(src: string): void {
    const a = new Audio(src)
    a.volume = 1
    this.voice = a
    const next = () => {
      if (this.voice !== a) return
      this.voice = null
      const p = this.pending
      this.pending = null
      if (p && this.active && this.on) this.playVoice(p)
    }
    a.addEventListener('ended', next)
    a.addEventListener('error', next)            // a missing line (not generated) is simply skipped
    a.play().catch(() => next())
  }

  /** Call when a scene starts while the intro is playing. */
  scene(sceneId: string, lang: string): void {
    this.active = true
    if (!this.on) return
    if (this.music.paused) this.music.play().catch(() => { /* autoplay refused: stay silent */ })
    const src = this.url(sceneId, lang)
    if (!src) return
    if (this.voice && !this.voice.paused && !this.voice.ended) this.pending = src
    else this.playVoice(src)
  }

  pause(): void {
    this.music.pause()
    this.voice?.pause()
  }

  resume(): void {
    if (!this.on || !this.active) return
    this.music.play().catch(() => {})
    this.voice?.play().catch(() => {})
  }

  setOn(on: boolean): void {
    this.on = on
    rememberSound(on)
    if (on) this.resume()
    else this.pause()
  }

  stop(): void {
    this.active = false
    this.pending = null
    this.voice?.pause()
    this.voice = null
    this.music.pause()
    this.music.currentTime = 0
  }
}
