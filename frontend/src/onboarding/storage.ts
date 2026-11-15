// Per-browser preferences. localStorage can be missing or throw (private mode,
// sandboxed frames), so every access is guarded and the app still works without it.
import type { UiLang } from './i18n'

const KEY_LANG = 'earth-senses.lang'
const KEY_SEEN = 'earth-senses.intro-seen'
const KEY_VARIANT = 'earth-senses.intro-variant'
/** Bump when the intro changes enough that returning visitors should see it again. */
export const INTRO_VERSION = '1'

export type VariantId = 'teaser' | 'explainer' | 'hero'

function get(key: string): string | null {
  try { return window.localStorage.getItem(key) } catch { return null }
}
function set(key: string, value: string): void {
  try { window.localStorage.setItem(key, value) } catch { /* not persisted; nothing else to do */ }
}

export const prefs = {
  lang(): UiLang | null {
    const v = get(KEY_LANG)
    return v === 'en' || v === 'ru' || v === 'kk' ? v : null
  },
  setLang(l: UiLang): void { set(KEY_LANG, l) },
  introSeen(): boolean { return get(KEY_SEEN) === INTRO_VERSION },
  setIntroSeen(): void { set(KEY_SEEN, INTRO_VERSION) },
  variant(): VariantId | null {
    const v = get(KEY_VARIANT)
    return v === 'teaser' || v === 'explainer' || v === 'hero' ? v : null
  },
  setVariant(v: VariantId): void { set(KEY_VARIANT, v) },
}
