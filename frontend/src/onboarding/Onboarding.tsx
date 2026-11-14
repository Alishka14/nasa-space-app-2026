// Splash -> language -> intro -> app, over one shared globe. Loaded lazily, so
// three.js and the textures never weigh on the main application bundle.
import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import EarthCanvas from './earth/EarthCanvas'
import type { EarthController } from './earth/types'
import Splash from './Splash'
import LanguageSelect from './LanguageSelect'
import IntroPlayer from './intro/IntroPlayer'
import { getVariant } from './content/scripts'
import { makeT, type UiLang } from './i18n'
import type { VariantId } from './storage'
import './onboarding.css'

export type Step = 'splash' | 'language' | 'intro'

interface Props {
  lang: UiLang
  previousLang: UiLang | null
  variant: VariantId
  start: Step
  capture?: boolean
  onLang: (l: UiLang) => void
  onVariant: (v: VariantId) => void
  /** Called when the visitor reaches the app: after the intro, or by skipping. */
  onDone: (how: 'finished' | 'skipped') => void
}

function prefersReducedMotion(): boolean {
  try { return window.matchMedia('(prefers-reduced-motion: reduce)').matches } catch { return false }
}

export default function Onboarding({ lang, previousLang, variant, start, capture = false, onLang, onVariant, onDone }: Props) {
  const [step, setStep] = useState<Step>(start)
  const [earth, setEarth] = useState<EarthController | null>(null)
  const [progress, setProgress] = useState(0)
  const [ready, setReady] = useState(false)
  const [leaving, setLeaving] = useState(false)
  const reduced = useMemo(prefersReducedMotion, [])
  const t = useMemo(() => makeT(lang), [lang])
  const doneOnce = useRef(false)

  // Camera for the screens that are not the intro.
  useEffect(() => {
    if (!earth) return
    if (step === 'splash') {
      // Earth rises from the bottom of the frame; the title sits above it in space.
      earth.setView({ lat: 0, lon: 10, dist: 4.4, y: -0.62 }, 0)
      earth.setOverlays({ coast: 0, graticule: 0, marker: 0, tint: 0 }, 0)
      earth.setView({ lat: 18, lon: 45, dist: 2.75, y: -0.47, spin: 4 }, 7)
    } else if (step === 'language') {
      earth.setView({ lat: 36, lon: 72, dist: 3.05, x: 0.23, spin: 3 }, 2.4)
      earth.setOverlays({ coast: 0.55, graticule: 0.25, marker: 1, tint: 0.35 }, 1.6)
    }
  }, [earth, step])

  const finish = useCallback((how: 'finished' | 'skipped') => {
    if (doneOnce.current) return
    doneOnce.current = true
    if (capture) return onDone(how)
    setLeaving(true)
    window.setTimeout(() => onDone(how), reduced ? 50 : 650)
  }, [capture, onDone, reduced])

  const toLanguage = useCallback(() => setStep(s => (s === 'splash' ? 'language' : s)), [])

  return (
    <div className={'es-onboarding' + (leaving ? ' es-leaving' : '') + (capture ? ' es-capture' : '')} lang={lang}
         role="dialog" aria-modal="true" aria-label="EARTH SENSES">
      <EarthCanvas onController={setEarth} onProgress={setProgress} onReady={() => setReady(true)}
                   reducedMotion={reduced} fallbackLabel={t('earth.fallback')} />
      <div className="es-vignette" aria-hidden="true" />
      {step === 'splash' && (
        <Splash lang={lang} progress={progress} ready={ready} reducedMotion={reduced}
                onContinue={toLanguage} onSkip={() => finish('skipped')} />
      )}
      {step === 'language' && (
        <LanguageSelect lang={lang} previous={previousLang} variant={variant} onLang={onLang} onVariant={onVariant}
                        onStart={() => setStep('intro')} onSkip={() => finish('skipped')} />
      )}
      {step === 'intro' && (
        <IntroPlayer key={variant + lang} variant={getVariant(variant)} lang={lang} earth={earth} capture={capture}
                     onFinish={() => finish('finished')} onSkip={() => finish('skipped')} />
      )}
    </div>
  )
}
