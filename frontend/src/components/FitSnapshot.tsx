import { useEffect, useMemo, useState } from 'react'

type FitSnapshotProps = {
  apiBase: string
  targetCountry: string
}

type ReadinessModule = {
  label: string
  ready: boolean
  completed_fields: number
  required_fields: number
  missing_fields: string[]
}

type ReadinessResponse = {
  modules: Record<string, ReadinessModule>
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

function readinessPercent(module?: ReadinessModule) {
  if (!module || module.required_fields <= 0) return 0
  return Math.round((module.completed_fields / module.required_fields) * 100)
}

function toneForStatus(value: string) {
  const normalized = value.toLowerCase()
  if (
    normalized.includes('ready') ||
    normalized.includes('shortage') ||
    normalized.includes('domestic') ||
    normalized.includes('free_movement') ||
    normalized.includes('portable_income_comparable')
  ) return 'positive'

  if (
    normalized.includes('blocked') ||
    normalized.includes('missing') ||
    normalized.includes('insufficient') ||
    normalized.includes('unmapped')
  ) return 'warning'

  return 'neutral'
}

export default function FitSnapshot({
  apiBase,
  targetCountry,
}: FitSnapshotProps) {
  const [state, setState] = useState<FitState>(EMPTY)
  const [readiness, setReadiness] = useState<ReadinessResponse | null>(null)

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
      fetch(`${apiBase}/api/profile/readiness`, { signal }).then((r) => r.json()),
    ]).then((results) => {
      if (signal.aborted) return

      const [legal, language, career, financial, ttv, readinessResult] = results

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

      if (readinessResult.status === 'fulfilled') {
        setReadiness(readinessResult.value)
      }
    })

    return () => controller.abort()
  }, [apiBase, targetCountry])

  const modules = useMemo(() => ({
    legal: readiness?.modules?.legal_fit,
    language: readiness?.modules?.language_fit,
    career: readiness?.modules?.career_fit,
    financial: readiness?.modules?.financial_fit,
  }), [readiness])

  const items = [
    ['LegalFit', state.legal, readinessPercent(modules.legal)],
    ['LanguageFit', state.language, readinessPercent(modules.language)],
    ['CareerFit', state.career, readinessPercent(modules.career)],
    ['FinancialFit', state.financial, readinessPercent(modules.financial)],
  ] as const

  return (
    <section className="fitSnapshot" aria-label="Personal fit snapshot">
      <div className="mockPanelHeader">
        <div>
          <div className="label">PERSONAL FIT SNAPSHOT</div>
          <strong>{targetCountry} · profile readiness</strong>
        </div>
        <span>real inputs · no fit score</span>
      </div>

      <div className="fitSnapshotGrid mockFitGrid">
        {items.map(([label, value, percent]) => (
          <article className={`mockFitCard ${toneForStatus(value)}`} key={label}>
            <div
              className="readinessRing"
              style={{ '--progress': percent } as React.CSSProperties}
              aria-label={`${label} profile readiness ${percent}%`}
            >
              <span>{percent}</span>
            </div>
            <div>
              <small>{label}</small>
              <strong>{display(value)}</strong>
              <p>{percent}% profile inputs complete</p>
            </div>
          </article>
        ))}

        <article className={`mockFitCard ttv ${toneForStatus(state.ttv)}`}>
          <div className="readinessRing ttvRing">
            <span>—</span>
          </div>
          <div>
            <small>TTV</small>
            <strong>{display(state.ttv)}</strong>
            <p>Time estimate waits for complete evidence</p>
          </div>
        </article>
      </div>
    </section>
  )
}
