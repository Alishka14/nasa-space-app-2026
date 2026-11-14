import { useEffect, useState } from 'react'
import { api, type InvestigateBody } from '../api'
import { Card, type T } from './common'

export default function ReportView({ body, t }: { body: InvestigateBody; t: T }) {
  const [md, setMd] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  useEffect(() => {
    setMd(null); setError(null)
    api.report(body).then(r => setMd(r.markdown)).catch(e => setError(String(e.message ?? e)))
  }, [body])

  const download = () => {
    if (!md) return
    const url = URL.createObjectURL(new Blob([md], { type: 'text/markdown' }))
    const a = document.createElement('a')
    a.href = url
    a.download = `earth-senses-report-${body.latitude}-${body.longitude}-${body.start}-${body.end}.md`
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <Card title={t('tabReport')} right={<button className="primary small" onClick={download} disabled={!md}>{t('download')}</button>}>
      {error && <div className="banner error">{error}</div>}
      {!md && !error && <p className="muted">{t('working')}</p>}
      {md && <pre className="report">{md}</pre>}
    </Card>
  )
}
