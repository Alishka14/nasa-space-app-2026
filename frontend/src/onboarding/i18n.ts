// Onboarding strings (src/locales/*.json), intro scripts and number formatting.
// Numbers in any text are written as {fact_key} and filled from facts.json, so
// the intro, the docs and the subtitles can never disagree with the engine.
import en from '../locales/en.json'
import ru from '../locales/ru.json'
import kk from '../locales/kk.json'
import facts from './content/facts.json'

export type UiLang = 'en' | 'ru' | 'kk'
export const LANGS: UiLang[] = ['en', 'ru', 'kk']
export type MsgKey = keyof typeof en

const MESSAGES: Record<UiLang, Record<MsgKey, string>> = { en, ru, kk }

interface Fact { value: number; digits: number; signed: boolean }
const FACTS = facts as unknown as Record<string, Fact>

/** Locale-correct number: proper minus sign, decimal comma for Russian and Kazakh. */
export function formatNumber(value: number, digits: number, signed: boolean, lang: UiLang): string {
  const abs = Math.abs(value).toFixed(digits)
  const body = lang === 'en' ? abs : abs.replace('.', ',')
  if (value < 0 && Number(abs) !== 0) return '−' + body
  return signed && value > 0 ? '+' + body : body
}

export function factText(key: string, lang: UiLang): string {
  const f = FACTS[key]
  if (!f || typeof f.value !== 'number') return `{${key}}`
  return formatNumber(f.value, f.digits, f.signed, lang)
}

export function factValue(key: string): number {
  return FACTS[key]?.value ?? NaN
}

/** Replace {fact} and {param} placeholders. Unknown placeholders stay visible on purpose. */
export function fill(text: string, lang: UiLang, params: Record<string, string | number> = {}): string {
  return text.replace(/\{([a-z0-9_]+)\}/gi, (whole, key: string) => {
    if (key in params) return String(params[key])
    return key in FACTS ? factText(key, lang) : whole
  })
}

export function makeT(lang: UiLang) {
  return (key: MsgKey, params?: Record<string, string | number>) => fill(MESSAGES[lang][key] ?? MESSAGES.en[key], lang, params)
}
export type T = ReturnType<typeof makeT>

export const HTML_LANG: Record<UiLang, string> = { en: 'en', ru: 'ru', kk: 'kk' }
