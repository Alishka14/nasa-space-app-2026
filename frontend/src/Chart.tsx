import { useEffect, useRef } from 'react'
import * as echarts from 'echarts'

/** ECharts host. The option object is built by pure functions in charts.ts. */
export default function Chart({ option, height, onClick }: {
  option: echarts.EChartsOption; height: number; onClick?: (params: unknown) => void
}) {
  const el = useRef<HTMLDivElement>(null)
  const inst = useRef<echarts.ECharts | null>(null)

  useEffect(() => {
    if (!el.current) return
    const chart = echarts.init(el.current, undefined, { renderer: 'canvas' })
    inst.current = chart
    const ro = new ResizeObserver(() => chart.resize())
    ro.observe(el.current)
    return () => { ro.disconnect(); chart.dispose(); inst.current = null }
  }, [])

  useEffect(() => { inst.current?.setOption(option, true) }, [option])

  useEffect(() => {
    const chart = inst.current
    if (!chart || !onClick) return
    chart.on('click', onClick)
    return () => { chart.off('click', onClick) }
  }, [onClick])

  return <div ref={el} style={{ width: '100%', height }} />
}
