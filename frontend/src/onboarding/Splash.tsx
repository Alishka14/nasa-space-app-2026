import { useEffect, useMemo, useState } from 'react'
import { makeT, type UiLang } from './i18n'

interface Props {
  lang: UiLang
  progress: number      // texture loading, 0–1
  ready: boolean        // globe textures loaded (or failed and fell back)
  reducedMotion: boolean
  onContinue: () => void
  onSkip: () => void
}

/**
 * Title card over the globe. Advances by itself once the globe is ready and the
 * title has been on screen long enough to read; any key or click advances sooner.
 */
export default function Splash({ lang, progress, ready, reducedMotion, onContinue, onSkip }: Props) {
  const t = useMemo(() => makeT(lang), [lang])
  const [elapsed, setElapsed] = useState(0)
  const minShow = reducedMotion ? 2.5 : 5.2
  const maxWait = 12

  useEffect(() => {
    const t0 = performance.now()
    const id = window.setInterval(() => setElapsed((performance.now() - t0) / 1000), 100)
    return () => window.clearInterval(id)
  }, [])

  useEffect(() => {
    if ((ready && elapsed >= minShow) || elapsed >= maxWait) onContinue()
  }, [ready, elapsed, minShow, onContinue])

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onSkip()
      else if (elapsed > 0.8) onContinue()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [elapsed, onContinue, onSkip])

  return (
    <div className={'es-splash' + (reducedMotion ? ' es-still' : '')} onClick={() => elapsed > 0.8 && onContinue()}>
      <div className="es-splash-center">
        <div className="es-kicker">{t('splash.kicker')}</div>
        <h1 className="es-wordmark" aria-label="EARTH SENSES">
          {'EARTH SENSES'.split('').map((ch, i) => (
            <span key={i} style={{ animationDelay: `${0.25 + i * 0.05}s` }}>{ch === ' ' ? ' ' : ch}</span>
          ))}
        </h1>
        <p className="es-tagline">{t('splash.tagline')}</p>
        <p className="es-motto">{t('splash.motto')}</p>
      </div>
      <div className="es-splash-foot">
        {!ready
          ? <div className="es-loading" role="status"><i style={{ width: `${Math.round(progress * 100)}%` }} />{t('splash.loading')} · {Math.round(progress * 100)}%</div>
          : <div className="es-hint">{t('splash.continue')}</div>}
        <button className="es-link" onClick={e => { e.stopPropagation(); onSkip() }}>{t('common.skipIntro')} →</button>
      </div>
    </div>
  )
}
