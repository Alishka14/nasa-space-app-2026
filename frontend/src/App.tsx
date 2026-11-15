import { useCallback, useEffect, useMemo, useState } from 'react'
import { api, type Catalog, type InvestigateBody, type Investigation, type Region } from './api'
import { LANG_LABEL, tr, type Lang } from './i18n'
import type { Mode } from './theme'
import MapPanel from './MapPanel'
import InvestigateView from './views/InvestigateView'
import GraphView from './views/GraphView'
import TimelineView from './views/TimelineView'
import CompareView from './views/CompareView'
import ReportView from './views/ReportView'
import EvidenceDrawer from './views/EvidenceDrawer'
import { placeNote, setSciLang, varDef, varName } from './sciI18n'

type Tab = 'investigate' | 'graph' | 'timeline' | 'compare' | 'report'

export interface AppProps {
  /** Controlled language (set by the onboarding); without it the app keeps its own. */
  lang?: Lang
  onLang?: (l: Lang) => void
  /** Re-opens the onboarding intro; the button is shown only when this is provided. */
  onReplayIntro?: () => void
}

export default function App({ lang: langProp, onLang, onReplayIntro }: AppProps = {}) {
  const [langState, setLangState] = useState<Lang>(langProp ?? 'en')
  const lang = langProp ?? langState
  const setLang = onLang ?? setLangState
  const [mode, setMode] = useState<Mode>('dark')
  const [tab, setTab] = useState<Tab>('investigate')
  const [catalog, setCatalog] = useState<Catalog | null>(null)
  const [bootError, setBootError] = useState<string | null>(null)

  const [lat, setLat] = useState(52.29)
  const [lon, setLon] = useState(76.97)
  const [name, setName] = useState('Pavlodar, Kazakhstan')
  const [start, setStart] = useState(2001)
  const [end, setEnd] = useState(2024)
  const [vars, setVars] = useState<string[]>(['T2M', 'RH2M', 'PRECTOTCORR'])
  const [fullBaseline, setFullBaseline] = useState(true)
  const [bStart, setBStart] = useState(2001)
  const [bEnd, setBEnd] = useState(2020)

  const [inv, setInv] = useState<Investigation | null>(null)
  const [body, setBody] = useState<InvestigateBody | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [evidenceId, setEvidenceId] = useState<string | null>(null)
  setSciLang(lang)   // scientific labels follow the interface language (engine sentences stay English)
  const t = useMemo(() => tr(lang), [lang])

  useEffect(() => { document.documentElement.dataset.theme = mode }, [mode])
  useEffect(() => {
    api.catalog().then(c => { setCatalog(c); setEnd(e => Math.min(e, c.last_complete_year)) })
      .catch(e => setBootError(String(e.message ?? e)))
  }, [])

  const region = catalog?.regions.find(r => Math.abs(r.latitude - lat) < 1e-9 && Math.abs(r.longitude - lon) < 1e-9)
  const pickRegion = useCallback((r: Region) => { setLat(r.latitude); setLon(r.longitude); setName(r.name) }, [])
  const pickPoint = useCallback((la: number, lo: number) => {
    setLat(la); setLon(lo); setName(`Custom point ${la.toFixed(2)}, ${lo.toFixed(2)}`)
  }, [])

  const run = async () => {
    const b: InvestigateBody = { latitude: lat, longitude: lon, start, end, variables: vars, region_name: name }
    if (!fullBaseline) { b.baseline_start = bStart; b.baseline_end = bEnd }
    setBusy(true); setError(null)
    try {
      setInv(await api.investigate(b)); setBody(b)
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e)); setInv(null); setBody(null)
    } finally { setBusy(false) }
  }

  const varList = (verified: boolean) => catalog && Object.entries(catalog.variables).filter(([, v]) => v.verified === verified)
    .map(([id, v]) => (
      <label key={id} className={'var' + (vars.includes(id) ? ' on' : '')} title={v.definition}>
        <input type="checkbox" checked={vars.includes(id)} onChange={() => toggleVar(id)} />
        <span><b>{varName(id, v.label)}</b> <code>{id}</code><small>{varDef(id, v.definition)}</small></span>
      </label>
    ))
  const toggleVar = (v: string) => setVars(cur => (cur.includes(v) ? cur.filter(x => x !== v) : [...cur, v]))
  const tabs: [Tab, string][] = [['investigate', t('tabInvestigate')], ['graph', t('tabGraph')], ['timeline', t('tabTimeline')],
                                 ['compare', t('tabCompare')], ['report', t('tabReport')]]
  const cachedHere = !!region && covered(region.cached_periods, start, end)

  return (
    <div className="app">
      <header className="top">
        <div className="brand">
          <div className="logo" aria-hidden="true" />
          <div>
            <h1>EARTH SENSES</h1>
            <p>{t('tagline')}</p>
          </div>
        </div>
        <nav className="tabs" role="tablist">
          {tabs.map(([id, label]) => (
            <button key={id} role="tab" aria-selected={tab === id} className={tab === id ? 'on' : ''} onClick={() => setTab(id)}>{label}</button>
          ))}
        </nav>
        <div className="toggles">
          <div className="lang-switch" role="radiogroup" aria-label={t('language')}>
            {(Object.keys(LANG_LABEL) as Lang[]).map(l => (
              <button key={l} role="radio" aria-checked={lang === l} className={lang === l ? 'on' : ''} onClick={() => setLang(l)}>{LANG_LABEL[l]}</button>
            ))}
          </div>
          {onReplayIntro && <button className="intro-btn" onClick={onReplayIntro} title={t('intro')}>▶ {t('intro')}</button>}
          <button onClick={() => setMode(mode === 'dark' ? 'light' : 'dark')} title="Theme">{mode === 'dark' ? '☀' : '☾'}</button>
        </div>
      </header>

      {bootError && <div className="banner error">Backend not reachable: {bootError}. Start it with <code>uvicorn earth_senses.api:app --app-dir backend</code>.</div>}

      <main>
        {tab === 'investigate' && (
          <div className="split">
            <aside className="panel controls">
              <h2>{t('where')}</h2>
              {catalog && <MapPanel regions={catalog.regions} lat={lat} lon={lon} mode={mode} onPick={pickPoint} onRegion={pickRegion} />}
              <p className="hint">{t('mapHint')}</p>
              <div className="row">
                <label>{t('latitude')}<input type="number" step="0.01" min={-90} max={90} value={lat}
                  onChange={e => pickPoint(Number(e.target.value), lon)} /></label>
                <label>{t('longitude')}<input type="number" step="0.01" min={-180} max={180} value={lon}
                  onChange={e => pickPoint(lat, Number(e.target.value))} /></label>
              </div>
              <p className="place">
                <strong>{name}</strong>
                <span className={'chip ' + (cachedHere ? 'ok' : 'warn')}>{cachedHere ? '● ' + t('cached') : '◌ ' + t('live')}</span>
              </p>
              {region && <p className="hint">{placeNote(region.note)}</p>}

              <h2>{t('what')}</h2>
              <div className="vars">{varList(true)}</div>
              <details className="more" open={vars.some(v => catalog && !catalog.variables[v]?.verified)}>
                <summary>{t('moreVars')}</summary>
                <div className="vars">{varList(false)}</div>
              </details>

              <h2>{t('when')}</h2>
              <div className="row">
                <label>{t('from')}<input type="number" min={catalog?.first_year ?? 1981} max={end} value={start} onChange={e => setStart(Number(e.target.value))} /></label>
                <label>{t('to')}<input type="number" min={start} max={catalog?.last_complete_year ?? 2025} value={end} onChange={e => setEnd(Number(e.target.value))} /></label>
              </div>
              <div className="presets">
                {[[2001, 2024], [1981, 2024], [1991, 2020]].map(([s, e]) => (
                  <button key={s + '-' + e} className={start === s && end === e ? 'on' : ''} onClick={() => { setStart(s); setEnd(e) }}>{s}–{e}</button>
                ))}
              </div>
              <label className="inline"><input type="checkbox" checked={fullBaseline} onChange={e => setFullBaseline(e.target.checked)} />
                {t('baseline')}: {t('baselineFull')}</label>
              {!fullBaseline && (
                <div className="row">
                  <label>{t('from')}<input type="number" value={bStart} onChange={e => setBStart(Number(e.target.value))} /></label>
                  <label>{t('to')}<input type="number" value={bEnd} onChange={e => setBEnd(Number(e.target.value))} /></label>
                </div>
              )}
              <button className="primary" onClick={run} disabled={busy || vars.length === 0 || !catalog}>{busy ? t('working') : t('investigate')}</button>
              {error && <div className="banner error" role="alert">{error}</div>}
              <p className="motto">{t('motto')}</p>
            </aside>
            <section className="results">
              {inv ? <InvestigateView inv={inv} t={t} mode={mode} onEvidence={setEvidenceId} />
                : <div className="empty panel"><h2>{t('emptyTitle')}</h2><p>{t('emptyBody')}</p></div>}
            </section>
          </div>
        )}
        {tab === 'graph' && (inv ? <GraphView inv={inv} t={t} mode={mode} onEvidence={setEvidenceId} /> : <Need t={t} />)}
        {tab === 'timeline' && (inv ? <TimelineView inv={inv} t={t} onEvidence={setEvidenceId} /> : <Need t={t} />)}
        {tab === 'compare' && catalog && <CompareView catalog={catalog} start={start} end={end} vars={vars} t={t} mode={mode} />}
        {tab === 'report' && (body ? <ReportView body={body} t={t} /> : <Need t={t} />)}
      </main>

      {inv && evidenceId && <EvidenceDrawer inv={inv} id={evidenceId} t={t} onClose={() => setEvidenceId(null)} onOpen={setEvidenceId} />}
    </div>
  )
}

/** Do the bundled files tile the requested years? Mirrors the backend's cache rule. */
function covered(periods: [number, number][], start: number, end: number): boolean {
  let cursor = start
  for (const [s, e] of [...periods].sort((a, b) => a[0] - b[0])) {
    if (s <= cursor && cursor <= e) cursor = e + 1
    if (cursor > end) return true
  }
  return cursor > end
}

function Need({ t }: { t: ReturnType<typeof tr> }) {
  return <div className="empty panel"><h2>{t('needRun')}</h2></div>
}
