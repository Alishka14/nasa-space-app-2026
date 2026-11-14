// Decides what a visitor sees first. First visit: splash -> language -> intro -> app.
// Returning visitor (intro already seen on this device): straight to the app, with
// an "Intro" button in the header to watch it again or change language.
// URL switches: ?intro (always show), ?intro=language (start at language), ?nointro
// (never show), ?capture&variant=hero&lang=ru (frame-exact video capture).
import { Suspense, lazy, useCallback, useState } from 'react'
import App from './App'
import type { Lang } from './i18n'
import { prefs, type VariantId } from './onboarding/storage'
import type { Step } from './onboarding/Onboarding'

const Onboarding = lazy(() => import('./onboarding/Onboarding'))

const VARIANTS: VariantId[] = ['teaser', 'explainer', 'hero']
const isLang = (x: string | null): x is Lang => x === 'en' || x === 'ru' || x === 'kk'

function setHtmlLang(l: Lang) { document.documentElement.lang = l }

export default function Root() {
  const q = new URLSearchParams(window.location.search)
  const capture = q.has('capture')
  const qLang = q.get('lang')
  const qVariant = q.get('variant') as VariantId | null
  const savedLang = prefs.lang()

  const [lang, setLangState] = useState<Lang>(() => {
    const l = isLang(qLang) ? qLang : savedLang ?? 'en'
    setHtmlLang(l)
    return l
  })
  const [variant, setVariantState] = useState<VariantId>(() =>
    qVariant && VARIANTS.includes(qVariant) ? qVariant : prefs.variant() ?? 'explainer')
  const [onboarding, setOnboarding] = useState<Step | null>(() => {
    if (capture) return 'intro'
    if (q.has('nointro')) return null
    if (q.get('intro') === 'language') return 'language'
    if (q.has('intro') || !prefs.introSeen()) return 'splash'
    return null
  })
  const [appShown, setAppShown] = useState(onboarding === null)

  const setLang = useCallback((l: Lang) => {
    setLangState(l)
    setHtmlLang(l)
    if (!capture) prefs.setLang(l)
  }, [capture])
  const setVariant = useCallback((v: VariantId) => { setVariantState(v); prefs.setVariant(v) }, [])
  const done = useCallback(() => {
    if (capture) return
    prefs.setIntroSeen()
    setOnboarding(null)
    setAppShown(true)
  }, [capture])

  return (
    <>
      {appShown && (
        <div className="app-host" inert={onboarding !== null} aria-hidden={onboarding !== null}>
          <App lang={lang} onLang={setLang} onReplayIntro={() => setOnboarding('language')} />
        </div>
      )}
      {onboarding && (
        <Suspense fallback={<div className="boot-screen" />}>
          <Onboarding lang={lang} previousLang={savedLang} variant={variant} start={onboarding} capture={capture}
                      onLang={setLang} onVariant={setVariant} onDone={done} />
        </Suspense>
      )}
    </>
  )
}
