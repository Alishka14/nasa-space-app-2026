// Pure option builders for ECharts. Rules followed throughout:
// one y-axis per panel (variables with different units get separate panels, never a
// dual axis); colour identifies the variable; sign uses a blue/red diverging pair;
// every chart has a hover layer; text stays in ink colours.
/* eslint-disable @typescript-eslint/no-explicit-any */
import type { EChartsOption } from 'echarts'
import { chrome, fmt, fmtP, MONTHS, seriesColor, type Mode } from './theme'

type Infos = Record<string, { label: string; display_units: string }>
const PANEL = 172
const LEFT = 62

export const stackedHeight = (n: number) => n * PANEL + 26

function axisStyle(mode: Mode) {
  const c = chrome[mode]
  return {
    axisLine: { lineStyle: { color: c.axis } }, axisTick: { lineStyle: { color: c.axis } },
    axisLabel: { color: c.muted, fontSize: 11 }, splitLine: { lineStyle: { color: c.grid } },
    nameTextStyle: { color: c.muted, fontSize: 11 },
  }
}

function tooltipStyle(mode: Mode) {
  const c = chrome[mode]
  return { backgroundColor: c.surface, borderColor: c.axis, textStyle: { color: c.ink, fontSize: 12 } }
}

/** One panel per variable, stacked, sharing the time axis and a linked crosshair. */
export function stackedSeries(x: string[], vars: string[], data: Record<string, (number | null)[]>, infos: Infos,
                              mode: Mode, opts: { zero?: boolean; monthly?: boolean } = {}): EChartsOption {
  const c = chrome[mode]
  const ax = axisStyle(mode)
  const n = vars.length
  return {
    animationDuration: 250,
    title: vars.map((v, i) => ({
      text: `${infos[v].label} (${infos[v].display_units})`, left: LEFT, top: i * PANEL,
      textStyle: { color: c.ink, fontSize: 12, fontWeight: 600 },
    })),
    grid: vars.map((_, i) => ({ left: LEFT, right: 18, top: 26 + i * PANEL, height: PANEL - 62 })),
    tooltip: {
      trigger: 'axis', ...tooltipStyle(mode),
      formatter: (ps: any) => {
        const head = opts.monthly ? ps[0].axisValue : ps[0].axisValue
        return `<b>${head}</b><br/>` + ps.map((p: any) =>
          `${p.marker}${p.seriesName}: <b>${fmt(p.value as number, 2, !!opts.zero)}</b> ${infos[vars[p.seriesIndex]].display_units}`).join('<br/>')
      },
    },
    axisPointer: { link: [{ xAxisIndex: 'all' }], lineStyle: { color: c.muted } },
    xAxis: vars.map((_, i) => ({
      type: 'category' as const, data: x, gridIndex: i, boundaryGap: false, ...ax,
      splitLine: { show: false },
      axisLabel: {
        ...ax.axisLabel, show: i === n - 1,
        interval: opts.monthly ? (idx: number) => x[idx].endsWith('-01') && Number(x[idx].slice(0, 4)) % 4 === 0 : 'auto',
        formatter: (val: string) => (opts.monthly ? val.slice(0, 4) : val),
      },
      axisTick: { show: false },
    })),
    yAxis: vars.map((_, i) => ({ type: 'value' as const, gridIndex: i, scale: true, splitNumber: 3, ...ax })),
    series: vars.map((v, i) => ({
      name: infos[v].label, type: 'line' as const, xAxisIndex: i, yAxisIndex: i, data: data[v], showSymbol: false,
      lineStyle: { width: opts.monthly ? 1.4 : 2, color: seriesColor(v, mode) }, itemStyle: { color: seriesColor(v, mode) },
      markLine: opts.zero ? { silent: true, symbol: 'none', label: { show: false },
                              lineStyle: { color: c.axis, type: 'solid' as const, width: 1 }, data: [{ yAxis: 0 }] } : undefined,
    })),
  }
}

export function climatology(vars: string[], clim: Record<string, number[]>, infos: Infos, mode: Mode): EChartsOption {
  return stackedSeries(MONTHS, vars, clim, infos, mode)
}

/** Annual means with the Theil-Sen line; the longer record, when available, sits behind in grey. */
export function annualTrends(vars: string[], trends: any, infos: Infos, mode: Mode): EChartsOption {
  const c = chrome[mode]
  const ax = axisStyle(mode)
  const n = vars.length
  const series: any[] = []
  let xmin = Infinity
  let xmax = -Infinity
  vars.forEach((v, i) => {
    const t = trends[v]
    const yrs: number[] = t.annual.years
    const s = t.summary
    const ctx = t.context
    const first = ctx ? ctx.annual.years[0] : yrs[0]
    xmin = Math.min(xmin, first)
    xmax = Math.max(xmax, yrs[yrs.length - 1])
    if (ctx) {
      series.push({ name: `${infos[v].label} — longer record`, type: 'line', xAxisIndex: i, yAxisIndex: i, showSymbol: false,
                    data: ctx.annual.years.map((y: number, k: number) => [y, ctx.annual.values[k]]),
                    lineStyle: { width: 1.5, color: c.muted }, itemStyle: { color: c.muted }, z: 1 })
    }
    series.push({ name: infos[v].label, type: 'line', xAxisIndex: i, yAxisIndex: i, symbol: 'circle', symbolSize: 7,
                  data: yrs.map((y, k) => [y, t.annual.values[k]]),
                  lineStyle: { width: 2, color: seriesColor(v, mode) }, itemStyle: { color: seriesColor(v, mode) }, z: 3 })
    const sen = s.theil_sen
    series.push({ name: `${infos[v].label} — Theil-Sen line`, type: 'line', xAxisIndex: i, yAxisIndex: i, showSymbol: false,
                  data: [yrs[0], yrs[yrs.length - 1]].map(y => [y, sen.intercept + sen.slope * y]),
                  lineStyle: { width: 2, color: c.ink, type: 'dashed' }, itemStyle: { color: c.ink }, z: 4, silent: true })
  })
  return {
    animationDuration: 250,
    title: vars.map((v, i) => {
      const s = trends[v].summary
      return {
        text: `${infos[v].label} (${infos[v].display_units})`,
        subtext: `${fmt(s.primary_slope)} ${trends[v].slope_units}, 95% CI ${fmt(s.primary_ci[0])} to ${fmt(s.primary_ci[1])} · p = ${fmtP(s.primary_p)} · q = ${fmtP(trends[v].q)}`,
        left: LEFT, top: i * (PANEL + 14) - 2, itemGap: 2,
        textStyle: { color: c.ink, fontSize: 12, fontWeight: 600 }, subtextStyle: { color: c.ink2, fontSize: 11 },
      }
    }),
    grid: vars.map((_, i) => ({ left: LEFT, right: 18, top: 40 + i * (PANEL + 14), height: PANEL - 62 })),
    tooltip: {
      trigger: 'axis', ...tooltipStyle(mode),
      formatter: (ps: any) => `<b>${ps[0].value[0]}</b><br/>` + ps.filter((p: any) => !p.seriesName.includes('Theil'))
        .map((p: any) => `${p.marker}${p.seriesName}: <b>${fmt(p.value[1], 2, false)}</b>`).join('<br/>'),
    },
    xAxis: vars.map((_, i) => ({ type: 'value' as const, gridIndex: i, min: xmin, max: xmax, minInterval: 1, ...ax,
                                 splitLine: { show: false }, axisLabel: { ...ax.axisLabel, show: i === n - 1, formatter: (v: number) => String(v) } })),
    yAxis: vars.map((_, i) => ({ type: 'value' as const, gridIndex: i, scale: true, splitNumber: 3, ...ax })),
    series,
  }
}
export const annualHeight = (n: number) => n * (PANEL + 14) + 30

function signColor(v: number | null, mode: Mode) {
  const c = chrome[mode]
  return v === null ? c.muted : v < 0 ? c.neg : c.pos
}

/** How the correlation changes as seasonality and trend are removed. */
export function correlationSteps(rel: any, mode: Mode): EChartsOption {
  const c = chrome[mode]
  const ax = axisStyle(mode)
  const rows = [
    ['Detrended anomalies', rel.detrended.pearson_r], ['Deseasonalized anomalies', rel.deseasonalized.pearson_r],
    ['Seasonal cycles alone', rel.seasonal_cycle_only.pearson_r], ['Raw monthly values', rel.raw.pearson_r],
  ] as [string, number][]
  return {
    animationDuration: 250,
    grid: { left: 168, right: 56, top: 8, bottom: 26 },
    tooltip: { trigger: 'item', ...tooltipStyle(mode),
               formatter: (p: any) => `${p.name}<br/>r = <b>${fmt(p.value, 3)}</b>` + (p.dataIndex === 0
                 ? `<br/>95% CI ${fmt(rel.detrended.ci95_adjusted[0], 2)} to ${fmt(rel.detrended.ci95_adjusted[1], 2)}<br/>effective n = ${rel.detrended.n_eff.toFixed(0)}` : '') },
    xAxis: { type: 'value', min: -1, max: 1, interval: 0.5, ...ax },
    yAxis: { type: 'category', data: rows.map(r => r[0]), ...ax, axisLabel: { color: c.ink2, fontSize: 12 }, axisTick: { show: false } },
    series: [{
      type: 'bar', barWidth: 14,
      data: rows.map(r => ({ value: r[1], itemStyle: { color: signColor(r[1], mode), borderRadius: r[1] < 0 ? [4, 0, 0, 4] : [0, 4, 4, 0] } })),
      label: { show: true, position: 'right', color: c.ink, fontSize: 12, formatter: (p: any) => fmt(p.value, 2) },
      markLine: { silent: true, symbol: 'none', label: { show: false }, lineStyle: { color: c.axis, type: 'solid', width: 1 }, data: [{ xAxis: 0 }] },
    }],
  }
}

/** Lag scan. Solid bars stay significant after correcting for the number of lags tried. */
export function lagScan(rel: any, mode: Mode): EChartsOption {
  const c = chrome[mode]
  const ax = axisStyle(mode)
  const rows: any[] = rel.lags.rows
  const m = Math.max(0.2, ...rows.map(r => Math.abs(r.r ?? 0))) * 1.15
  return {
    animationDuration: 250,
    grid: { left: 44, right: 12, top: 12, bottom: 40 },
    tooltip: { trigger: 'item', ...tooltipStyle(mode),
               formatter: (p: any) => { const r = rows[p.dataIndex]
                 return `lag ${r.lag > 0 ? '+' : ''}${r.lag} months<br/>r = <b>${fmt(r.r)}</b> (n = ${r.n})<br/>q = ${fmtP(r.q)}${r.q !== null && r.q < 0.05 ? ' — significant after correction' : ''}` } },
    xAxis: { type: 'category', data: rows.map(r => (r.lag > 0 ? `+${r.lag}` : String(r.lag))), ...ax, axisTick: { show: false },
             axisLabel: { ...ax.axisLabel, interval: 0 },
             name: `lag in months (+ pairs ${rel.x} with later ${rel.y})`, nameLocation: 'middle', nameGap: 26 },
    yAxis: { type: 'value', min: -m, max: m, splitNumber: 4, ...ax, axisLabel: { ...ax.axisLabel, formatter: (v: number) => v.toFixed(1) } },
    series: [{
      type: 'bar', barWidth: '58%',
      data: rows.map(r => ({ value: r.r, itemStyle: { color: signColor(r.r, mode), opacity: r.q !== null && r.q < 0.05 ? 1 : 0.32,
                                                       borderRadius: r.r < 0 ? [0, 0, 4, 4] : [4, 4, 0, 0] } })),
      markLine: { silent: true, symbol: 'none', label: { show: false }, lineStyle: { color: c.axis, type: 'solid', width: 1 }, data: [{ yAxis: 0 }] },
    }],
  }
}

export function seasonSplit(rel: any, mode: Mode): EChartsOption {
  const c = chrome[mode]
  const ax = axisStyle(mode)
  const names = ['DJF', 'MAM', 'JJA', 'SON']
  const labels = ['Winter DJF', 'Spring MAM', 'Summer JJA', 'Autumn SON']
  const vals = names.map(k => rel.by_season.seasons[k].r as number)
  return {
    animationDuration: 250,
    grid: { left: 44, right: 12, top: 22, bottom: 26 },
    tooltip: { trigger: 'item', ...tooltipStyle(mode),
               formatter: (p: any) => `${labels[p.dataIndex]}<br/>r = <b>${fmt(p.value)}</b><br/>adjusted p = ${fmtP(rel.by_season.seasons[names[p.dataIndex]].p_adjusted)}` },
    xAxis: { type: 'category', data: labels, ...ax, axisTick: { show: false }, axisLabel: { color: c.ink2, fontSize: 11, interval: 0 } },
    yAxis: { type: 'value', min: -1, max: 1, interval: 0.5, ...ax },
    series: [{
      type: 'bar', barWidth: 26,
      data: vals.map(v => ({ value: v, itemStyle: { color: signColor(v, mode), borderRadius: v < 0 ? [0, 0, 4, 4] : [4, 4, 0, 0] } })),
      label: { show: true, position: 'top', color: c.ink, fontSize: 12, formatter: (p: any) => fmt(p.value, 2) },
      markLine: { silent: true, symbol: 'none', label: { show: false }, lineStyle: { color: c.axis, type: 'solid', width: 1 }, data: [{ yAxis: 0 }] },
    }],
  }
}

/** Slope for every sub-period: does the answer survive a change of window? */
export function windowHeatmap(trend: any, mode: Mode): EChartsOption {
  const c = chrome[mode]
  const ax = axisStyle(mode)
  const rows: any[] = trend.window_sensitivity.windows
  const starts = [...new Set(rows.map(r => r.start))].sort((a, b) => a - b)
  const ends = [...new Set(rows.map(r => r.end))].sort((a, b) => a - b)
  const m = Math.max(...rows.map(r => Math.abs(r.slope))) || 1
  return {
    animationDuration: 250,
    grid: { left: 52, right: 86, top: 10, bottom: 44 },
    tooltip: { ...tooltipStyle(mode),
               formatter: (p: any) => { const r = rows[p.dataIndex]
                 return `${r.start}–${r.end} (${r.n} years)<br/>slope <b>${fmt(r.slope)}</b> ${trend.slope_units}<br/>Mann-Kendall p = ${fmtP(r.p)}` } },
    xAxis: { type: 'category', data: starts.map(String), name: 'first year', nameLocation: 'middle', nameGap: 26, ...ax, splitLine: { show: false } },
    yAxis: { type: 'category', data: ends.map(String), name: 'last year', ...ax, splitLine: { show: false } },
    visualMap: { type: 'continuous', min: -m, max: m, dimension: 2, right: 4, top: 'middle', itemHeight: 110, itemWidth: 10,
                 inRange: { color: [c.neg, c.mid, c.pos] }, textStyle: { color: c.muted, fontSize: 10 },
                 text: [`+${m.toFixed(3)}`, `−${m.toFixed(3)}`], calculable: false, seriesIndex: 0 },
    series: [
      { type: 'heatmap', data: rows.map(r => [String(r.start), String(r.end), r.slope]),
        itemStyle: { borderColor: c.surface, borderWidth: 2 }, emphasis: { itemStyle: { borderColor: c.ink } } },
      { type: 'scatter', silent: true, symbolSize: 5, itemStyle: { color: c.ink },
        data: rows.filter(r => r.p !== null && r.p < 0.05).map(r => [String(r.start), String(r.end)]) },
    ],
  }
}

/** Two places, same variable: annual means of each and their difference. */
export function compareSeries(item: any, nameA: string, nameB: string, mode: Mode): EChartsOption {
  const c = chrome[mode]
  const ax = axisStyle(mode)
  const col = seriesColor(item.variable, mode)
  const yrs: number[] = item.years
  const mk = (vals: number[]) => yrs.map((y, i) => [y, vals[i]])
  return {
    animationDuration: 250,
    legend: { top: 0, left: LEFT, textStyle: { color: c.ink2, fontSize: 11 }, itemWidth: 22, itemHeight: 8,
              data: [nameA, nameB, 'Difference (first − second)'] },
    grid: [{ left: LEFT, right: 18, top: 30, height: 120 }, { left: LEFT, right: 18, top: 186, height: 76 }],
    tooltip: { trigger: 'axis', ...tooltipStyle(mode),
               formatter: (ps: any) => `<b>${ps[0].value[0]}</b><br/>` + ps.map((p: any) => `${p.marker}${p.seriesName}: <b>${fmt(p.value[1], 2, false)}</b> ${item.units}`).join('<br/>') },
    axisPointer: { link: [{ xAxisIndex: 'all' }] },
    xAxis: [0, 1].map(i => ({ type: 'value' as const, gridIndex: i, min: yrs[0], max: yrs[yrs.length - 1], minInterval: 1, ...ax,
                              splitLine: { show: false }, axisLabel: { ...ax.axisLabel, show: i === 1, formatter: (v: number) => String(v) } })),
    yAxis: [0, 1].map(i => ({ type: 'value' as const, gridIndex: i, scale: true, splitNumber: 3, ...ax })),
    series: [
      { name: nameA, type: 'line', data: mk(item.a.annual), symbol: 'circle', symbolSize: 6, lineStyle: { width: 2, color: col }, itemStyle: { color: col } },
      { name: nameB, type: 'line', data: mk(item.b.annual), symbol: 'diamond', symbolSize: 7,
        lineStyle: { width: 2, color: c.ink2, type: 'dashed' }, itemStyle: { color: c.ink2 } },
      { name: 'Difference (first − second)', type: 'line', xAxisIndex: 1, yAxisIndex: 1, data: mk(item.difference.annual), showSymbol: false,
        lineStyle: { width: 2, color: c.muted }, itemStyle: { color: c.muted }, areaStyle: { color: c.muted, opacity: 0.12 } },
    ],
  }
}
