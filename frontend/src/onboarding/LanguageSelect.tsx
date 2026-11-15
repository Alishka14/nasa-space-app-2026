import { useEffect, useMemo, useRef, useState } from 'react'
import { LANGS, makeT, type UiLang } from './i18n'
import { VARIANTS, duration } from './content/scripts'
import type { VariantId } from './storage'

interface Props {
  lang: UiLang
  previous: UiLang | null
  variant: VariantId
  onLang: (l: UiLang) => void
  onVariant: (v: VariantId) => void
  onStart: () => void
  onSkip: () => void
}

const ORDER: VariantId[] = ['teaser', 'explainer', 'hero']

/** Language first, before any narration. Labels are each language's own name. */
export default function LanguageSelect({ lang, previous, variant, onLang, onVariant, onStart, onSkip }: Props) {
  const t = useMemo(() => makeT(lang), [lang])
  const [focus, setFocus] = useState(LANGS.indexOf(lang))
  const cards = useRef<(HTMLButtonElement | null)[]>([])

  useEffect(() => { cards.current[focus]?.focus() }, [focus])

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const n = ['1', '2', '3'].indexOf(e.key)
      if (n >= 0) { setFocus(n); onLang(LANGS[n]) }
      else if (e.key === 'ArrowDown' || e.key === 'ArrowRight') { e.preventDefault(); const i = (focus + 1) % 3; setFocus(i); onLang(LANGS[i]) }
      else if (e.key === 'ArrowUp' || e.key === 'ArrowLeft') { e.preventDefault(); const i = (focus + 2) % 3; setFocus(i); onLang(LANGS[i]) }
      else if (e.key === 'Escape') onSkip()
      else if (e.key === 'Enter' && (e.target as HTMLElement | null)?.classList.contains('es-lang-card')) {
        e.preventDefault(); onStart()
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [focus, onLang, onSkip, onStart])

  const all = LANGS.map(l => makeT(l))

  return (
    <div className="es-lang">
      <div className="es-lang-panel">
        <h1 className="es-lang-title">
          {all.map((tt, i) => <span key={LANGS[i]} className={LANGS[i] === lang ? 'on' : ''}>{tt('lang.title')}</span>)}
        </h1>
        <div className="es-lang-cards" role="radiogroup" aria-label={t('lang.title')}>
          {LANGS.map((l, i) => {
            const tl = all[i]
            const selected = l === lang
            return (
              <button key={l} ref={el => { cards.current[i] = el }} role="radio" aria-checked={selected} lang={l}
                      className={'es-lang-card' + (selected ? ' on' : '')}
                      onClick={() => { setFocus(i); onLang(l) }} onDoubleClick={onStart}>
                <span className="es-lang-num">{i + 1}</span>
                <span className="es-lang-name">{tl('meta.languageName')}</span>
                <span className="es-lang-sub">{tl('meta.continueIn')}</span>
                {previous === l && <span className="es-lang-prev">{tl('lang.previous')}</span>}
              </button>
            )
          })}
        </div>

        <div className="es-variant">
          <span className="es-variant-label">{t('lang.introLength')}</span>
          <div className="es-variant-chips" role="radiogroup" aria-label={t('lang.introLength')}>
            {ORDER.map(id => {
              const v = VARIANTS.find(x => x.id === id)!
              return (
                <button key={id} role="radio" aria-checked={variant === id} className={variant === id ? 'on' : ''} onClick={() => onVariant(id)}>
                  {t(`lang.variant.${id}`)} · {t('lang.seconds', { n: Math.round(duration(v)) })}
                </button>
              )
            })}
          </div>
        </div>

        <div className="es-lang-actions">
          <button className="es-primary" onClick={onStart}>{t('lang.start')} →</button>
          <button className="es-link" onClick={onSkip}>{t('common.skipIntro')}</button>
        </div>
        <p className="es-small">{t('lang.saved')}</p>
        <p className="es-small es-keys">{t('lang.keys')}</p>
      </div>
    </div>
  )
}
