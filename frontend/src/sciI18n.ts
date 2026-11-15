// Russian and Kazakh for the fixed scientific labels the engine sends in English: variable names and
// definitions, verdicts, record statuses, statistic labels, units and place notes. The engine's own
// sentences (conclusions, evidence text) stay in English, as the interface says. Unknown strings
// fall back to the English original, so nothing disappears.
import type { Lang } from './i18n'

let cur: Lang = 'en'
export const setSciLang = (l: Lang): void => { cur = l }
type RK = { ru: string; kk: string }
const pick = (m: Record<string, RK>, key: string, en: string): string =>
  cur === 'en' ? en : (m[key]?.[cur] ?? en)

const VARS: Record<string, { name: RK; def: RK }> = {
  T2M: { name: { ru: 'Температура воздуха (2 м)', kk: 'Ауа температурасы (2 м)' },
    def: { ru: 'Средняя температура воздуха в двух метрах над землёй — на этой высоте её измеряют метеостанции.',
      kk: 'Жерден екі метр биіктіктегі ауаның орташа температурасы — метеостанциялар осы биіктікте өлшейді.' } },
  RH2M: { name: { ru: 'Относительная влажность (2 м)', kk: 'Салыстырмалы ылғалдылық (2 м)' },
    def: { ru: 'Насколько воздух близок к насыщению водяным паром, в процентах. Зависит и от количества влаги, и от температуры.',
      kk: 'Ауаның су буымен қанығуға қаншалықты жақын екені, пайызбен. Ылғал мөлшеріне де, температураға да байланысты.' } },
  PRECTOTCORR: { name: { ru: 'Осадки (с коррекцией)', kk: 'Жауын-шашын (түзетілген)' },
    def: { ru: 'Дождь и снег (в пересчёте на воду) за сутки, в среднем за месяц. Умножьте на число дней в месяце, чтобы получить месячную сумму в миллиметрах.',
      kk: 'Тәулігіне жаңбыр мен қар (су есебімен), ай бойынша орташа. Айлық қосындыны миллиметрмен алу үшін айдағы күн санына көбейтіңіз.' } },
  QV2M: { name: { ru: 'Удельная влажность (2 м)', kk: 'Меншікті ылғалдылық (2 м)' },
    def: { ru: 'Масса водяного пара на массу влажного воздуха; в отличие от относительной влажности не меняется только оттого, что воздух нагрелся или остыл.',
      kk: 'Ылғалды ауа массасына шаққандағы су буының массасы; салыстырмалы ылғалдылықтан айырмашылығы — ауа жылынғаннан не суығаннан ғана өзгермейді.' } },
}
export const varName = (code: string, en: string): string => (cur === 'en' ? en : VARS[code]?.name[cur] ?? en)
export const varDef = (code: string, en: string): string => (cur === 'en' ? en : VARS[code]?.def[cur] ?? en)

const VERDICTS: Record<string, RK> = {
  ROBUST_TREND: { ru: 'Устойчивый тренд', kk: 'Тұрақты тренд' },
  FRAGILE_TREND: { ru: 'Ненадёжно — не установлено', kk: 'Тұрақсыз — дәлелденбеген' },
  NO_SIGNIFICANT_TREND_DETECTED: { ru: 'Значимый тренд не обнаружен', kk: 'Мәнді тренд анықталмады' },
  SUPPORTED: { ru: 'Связь подтверждена', kk: 'Байланыс расталды' },
  WEAK: { ru: 'Слабая связь', kk: 'Әлсіз байланыс' },
  INCONCLUSIVE: { ru: 'Не определено', kk: 'Нақты емес' },
  NOT_SUPPORTED: { ru: 'Не подтверждено', kk: 'Расталмады' },
  LAGGED_ASSOCIATION_DETECTED: { ru: 'Связь с запаздыванием обнаружена', kk: 'Кешіккен байланыс анықталды' },
  NO_LAGGED_ASSOCIATION_DETECTED: { ru: 'Связь с запаздыванием не обнаружена', kk: 'Кешіккен байланыс анықталмады' },
  UNTESTED: { ru: 'Не проверено', kk: 'Тексерілмеген' },
  CHECKS_PASSED: { ru: 'Проверки данных пройдены', kk: 'Деректер тексерісі өтті' },
  OPPOSITE_SIGNIFICANT_TRENDS: { ru: 'Значимые тренды противоположны', kk: 'Мәнді трендтер қарама-қарсы' },
  REGIONS_DIVERGE: { ru: 'Регионы расходятся', kk: 'Аймақтар ажырайды' },
  OPPOSITE_SIGNS_NOT_SIGNIFICANT: { ru: 'Знаки противоположны, незначимо', kk: 'Таңбалары қарама-қарсы, мәнсіз' },
  NO_SIGNIFICANT_DIFFERENCE_DETECTED: { ru: 'Значимой разницы нет', kk: 'Мәнді айырмашылық жоқ' },
  DERIVED_VARIABLE_CONFIRMED: { ru: 'Вычислена из других переменных', kk: 'Басқа айнымалылардан есептелген' },
  DERIVED_VARIABLE_CHECK_INCONCLUSIVE: { ru: 'Проверка производной переменной не дала ответа', kk: 'Туынды айнымалы тексерісі нақты емес' },
}
export const verdictLabel = (code: string, en: string): string => pick(VERDICTS, code, en)

const STATUS: Record<string, RK> = {
  OBSERVED: { ru: 'НАБЛЮДЕНИЕ', kk: 'БАҚЫЛАУ' },
  HYPOTHESIS: { ru: 'ГИПОТЕЗА', kk: 'ГИПОТЕЗА' },
}
export const statusLabel = (code: string): string => pick(STATUS, code, code)
export const replicatedLabel = (n: number): string =>
  cur === 'ru' ? `✔ воспроизведено значений: ${n}` : cur === 'kk' ? `✔ қайталанған мәндер: ${n}` : `✔ ${n} ${n === 1 ? 'value' : 'values'} replicated`

const STATS: Record<string, RK> = {
  '95% CI': { ru: '95% дов. интервал', kk: '95% сенім аралығы' },
  'p (adjusted)': { ru: 'p (с поправкой)', kk: 'p (түзетілген)' },
  'per decade': { ru: 'за 10 лет', kk: '10 жылға' },
  to: { ru: 'до', kk: '—' },
  Year: { ru: 'Год', kk: 'Жыл' },
}
export const statLabel = (en: string): string => pick(STATS, en, en)

const UNITS: Record<string, RK> = {
  '°C/year': { ru: '°C/год', kk: '°C/жыл' },
  'percentage points/year': { ru: 'п.п./год', kk: 'п.т./жыл' },
  'mm/day per year': { ru: 'мм/сут за год', kk: 'мм/тәул. жылына' },
  'mm/day': { ru: 'мм/сут', kk: 'мм/тәул.' },
  'mm/year per year': { ru: 'мм/год за год', kk: 'мм/жыл жылына' },
  'g/kg per year': { ru: 'г/кг за год', kk: 'г/кг жылына' },
}
export const unitLabel = (en: string): string => pick(UNITS, en, en)

const PLACES: Record<string, RK> = {
  'Steppe on the Irtysh river; strongly continental climate.': {
    ru: 'Степь на реке Иртыш; резко континентальный климат.', kk: 'Ертіс өзеніндегі дала; күрт континенттік климат.' },
  'Foothills of the Tien Shan. The MERRA-2 grid cell here averages high mountains and plain: its mean elevation is far above the city, so values describe the cell, not the city.': {
    ru: 'Предгорья Тянь-Шаня. Ячейка MERRA-2 здесь усредняет высокие горы и равнину: её средняя высота намного выше города, поэтому значения описывают ячейку, а не город.',
    kk: 'Тянь-Шань бөктері. Мұндағы MERRA-2 торы биік таулар мен жазықты орташалайды: оның орташа биіктігі қаладан әлдеқайда жоғары, сондықтан мәндер қаланы емес, торды сипаттайды.' },
  'Northern steppe. Not in the bundled cache: needs a live NASA request.': {
    ru: 'Северная степь. Нет в сохранённых данных: нужен запрос к NASA.', kk: 'Солтүстік дала. Сақталған деректерде жоқ: NASA-ға сұрау керек.' },
  'Former Aral Sea shore. Not in the bundled cache: needs a live NASA request.': {
    ru: 'Бывший берег Аральского моря. Нет в сохранённых данных: нужен запрос к NASA.', kk: 'Арал теңізінің бұрынғы жағасы. Сақталған деректерде жоқ: NASA-ға сұрау керек.' },
}
export const placeNote = (en: string): string => pick(PLACES, en, en)
