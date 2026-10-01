import { useEffect, useState } from 'react'

type FitSnapshotProps = {
  apiBase: string
  targetCountry: string
}

type FitState = {
  legal: string
  language: string
  career: string
  financial: string
  ttv: string
}

const EMPTY: FitState = {
  legal: 'loading',
  language: 'loading',
  career: 'loading',
  financial: 'loading',
  ttv: 'loading',
}

function display(value: string) {
  return value.replaceAll('_', ' ')
}

export default function FitSnapshot({
  apiBase,
  targetCountry,
}: FitSnapshotProps) {
  const [state, setState] = useState<FitState>(EMPTY)

  useEffect(() => {
    const controller = new AbortController()
    const signal = controller.signal
    setState(EMPTY)

    Promise.allSettled([
      fetch(`${apiBase}/api/countries/${targetCountry}/legal-fit`, { signal }).then((r) => r.json()),
      fetch(`${apiBase}/api/countries/${targetCountry}/language-fit`, { signal }).then((r) => r.json()),
      fetch(`${apiBase}/api/countries/${targetCountry}/career-fit`, { signal }).then((r) => r.json()),
      fetch(`${apiBase}/api/countries/${targetCountry}/financial-fit`, { signal }).then((r) => r.json()),
      fetch(`${apiBase}/api/countries/${targetCountry}/ttv`, { signal }).then((r) => r.json()),
    ]).then((results) => {
      if (signal.aborted) return

      const [legal, language, career, financial, ttv] = results

      setState({
        legal: legal.status === 'fulfilled' ? legal.value.status : 'unavailable',
        language: language.status === 'fulfilled' ? language.value.status : 'unavailable',
        career: career.status === 'fulfilled'
          ? career.value.market_signal ?? career.value.status
          : 'unavailable',
        financial: financial.status === 'fulfilled' ? financial.value.status : 'unavailable',
        ttv: ttv.status === 'fulfilled'
          ? ttv.value.ready_for_time_estimate
            ? 'ready'
            : 'blocked'
          : 'unavailable',
      })
    })

    return () => controller.abort()
  }, [apiBase, targetCountry])

  const items = [
    ['Legal', state.legal],
    ['Language', state.language],
    ['Career', state.career],
    ['Financial', state.financial],
    ['TTV', state.ttv],
  ]

  return (
    <section className="fitSnapshot" aria-label="Personal fit snapshot">
      <div className="comparePanelHeader">
        <div>
          <div className="label">PERSONAL FIT</div>
          <strong>Snapshot · {targetCountry}</strong>
        </div>
        <span>profile-aware</span>
      </div>

      <div className="fitSnapshotGrid">
        {items.map(([label, value]) => (
          <div key={label}>
            <span>{label}</span>
            <strong>{display(value)}</strong>
          </div>
        ))}
      </div>
    </section>
  )
}
