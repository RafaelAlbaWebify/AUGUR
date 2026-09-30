import { useEffect, useMemo, useState } from 'react'

type Health = {
  status: string
  phase: number
  version: string
  datastores: {
    sqlite: boolean
    duckdb: boolean
  }
}

type Trend = {
  direction: string
  interpretation: string
  confidence: string
  slope_per_year: number | null
  pct_change_1y: number | null
  pct_change_3y: number | null
  pct_change_5y: number | null
  years_used: number
  target_status: string | null
}

type Indicator = {
  country_iso3: string
  indicator_id: string
  name: string
  dimension: string
  period: number
  value: number
  unit: string
  source_id: string
  retrieved_at?: string
  source_updated_at?: string | null
  trend?: Trend
  interpretation_policy?: string
  target_min?: number | null
  target_max?: number | null
  sourceQuality?: SourceQualityItem
}

type Snapshot = {
  country_iso3: string
  observation_count: number
  indicators: Indicator[]
}

type TrendsResponse = {
  country_iso3: string
  indicator_count: number
  indicators: Indicator[]
}

type Signal = {
  indicator_id: string
  name: string
  direction: string
  confidence: string
  pct_change_5y: number | null
}

type DimensionAssessment = {
  trajectory: string
  confidence: string
  indicator_count: number
  directional_indicator_count: number
  coverage: number
  improving_signals: Signal[]
  deteriorating_signals: Signal[]
  stable_signals: Signal[]
  contextual_signals: Signal[]
}

type AssessmentResponse = {
  country_iso3: string
  method: string
  dimensions: Record<string, DimensionAssessment>
}

type SourceQualityItem = {
  indicator_id: string
  name: string
  dimension: string
  unit: string
  source_count: number
  preferred_source_id: string
  preferred_source_name: string
  preferred_period: number
  preferred_value: number
  freshest_period: number
  period_spread: number
  disagreement_pct: number | null
}

type SourceQualityResponse = {
  country_iso3: string
  indicators: SourceQualityItem[]
}

const API_BASE = 'http://127.0.0.1:8020'

const dimensionOrder = [
  'prosperity',
  'productive_capacity',
  'demography',
  'fiscal',
]

const dimensionLabels: Record<string, string> = {
  prosperity: 'Prosperity',
  productive_capacity: 'Productive capacity',
  demography: 'Demography',
  fiscal: 'Fiscal sustainability',
}

function formatValue(value: number, unit: string) {
  if (unit === 'percent' || unit === 'percent_gdp') return `${value.toFixed(1)}%`
  if (unit === 'persons') return new Intl.NumberFormat('en-US', { maximumFractionDigits: 0 }).format(value)
  if (unit === 'births_per_woman') return value.toFixed(2)
  if (unit === 'constant_2015_usd_per_person') {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      maximumFractionDigits: 0,
    }).format(value)
  }
  if (unit === 'constant_2015_usd') {
    return new Intl.NumberFormat('en-US', {
      notation: 'compact',
      maximumFractionDigits: 2,
    }).format(value)
  }
  if (unit === 'usd_ppp_per_hour') {
    return `${value.toFixed(1)} USD/h PPP`
  }
  return new Intl.NumberFormat('en-US', { maximumFractionDigits: 2 }).format(value)
}

function trendSymbol(direction?: string) {
  if (!direction || direction === 'unknown') return '·'
  if (direction === 'stable') return '→'
  if (direction === 'increase' || direction === 'strong_increase') return '↗'
  return '↘'
}

function trendLabel(trend?: Trend) {
  if (!trend) return 'Trend pending'
  if (trend.interpretation === 'improving') return 'Improving'
  if (trend.interpretation === 'deteriorating') return 'Deteriorating'
  if (trend.interpretation === 'within_target') return 'Within target'
  if (trend.direction === 'stable') return 'Stable'
  return 'Contextual'
}

function targetStatusLabel(status?: string | null) {
  if (!status) return null
  if (status === 'within_target') return 'Within target'
  if (status === 'above_target') return 'Above target'
  if (status === 'below_target') return 'Below target'
  return status
}

function changeLabel(value: number | null) {
  if (value === null) return '—'
  const sign = value > 0 ? '+' : ''
  return `${sign}${value.toFixed(1)}%`
}

export default function App() {
  const [health, setHealth] = useState<Health | null>(null)
  const [snapshot, setSnapshot] = useState<Snapshot | null>(null)
  const [trends, setTrends] = useState<TrendsResponse | null>(null)
  const [assessment, setAssessment] = useState<AssessmentResponse | null>(null)
  const [sourceQuality, setSourceQuality] = useState<SourceQualityResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    Promise.all([
      fetch(`${API_BASE}/api/health`).then(async (response) => {
        if (!response.ok) throw new Error(`Health HTTP ${response.status}`)
        return response.json()
      }),
      fetch(`${API_BASE}/api/countries/ESP/snapshot`).then(async (response) => {
        if (!response.ok) throw new Error(`Snapshot HTTP ${response.status}`)
        return response.json()
      }),
      fetch(`${API_BASE}/api/countries/ESP/trends`).then(async (response) => {
        if (!response.ok) throw new Error(`Trends HTTP ${response.status}`)
        return response.json()
      }),
      fetch(`${API_BASE}/api/countries/ESP/assessment`).then(async (response) => {
        if (!response.ok) throw new Error(`Assessment HTTP ${response.status}`)
        return response.json()
      }),
      fetch(`${API_BASE}/api/countries/ESP/source-quality`).then(async (response) => {
        if (!response.ok) throw new Error(`Source quality HTTP ${response.status}`)
        return response.json()
      }),
    ])
      .then(([healthData, snapshotData, trendsData, assessmentData, sourceQualityData]) => {
        setHealth(healthData)
        setSnapshot(snapshotData)
        setTrends(trendsData)
        setAssessment(assessmentData)
        setSourceQuality(sourceQualityData)
      })
      .catch((err) => setError(String(err)))
  }, [])

  const grouped = useMemo(() => {
    const groups: Record<string, Indicator[]> = {}
    const trendById = new Map((trends?.indicators ?? []).map((item) => [item.indicator_id, item]))
    const qualityById = new Map((sourceQuality?.indicators ?? []).map((item) => [item.indicator_id, item]))

    for (const indicator of snapshot?.indicators ?? []) {
      const trendItem = trendById.get(indicator.indicator_id)
      const enriched = {
        ...indicator,
        trend: trendItem?.trend,
        interpretation_policy: trendItem?.interpretation_policy,
        target_min: trendItem?.target_min,
        target_max: trendItem?.target_max,
        sourceQuality: qualityById.get(indicator.indicator_id),
      }
      groups[indicator.dimension] ??= []
      groups[indicator.dimension].push(enriched)
    }

    return groups
  }, [snapshot, trends, sourceQuality])

  return (
    <main className="shell">
      <header>
        <div>
          <div className="eyebrow">COUNTRY TRAJECTORY & PERSONAL FIT</div>
          <h1>AUGUR</h1>
          <p className="subtitle">Interpret present signals. Explore possible futures.</p>
        </div>

        <div className={`status ${health?.status === 'ok' ? 'ok' : ''}`}>
          <span className="dot" />
          {health ? `Phase ${health.phase} · ${health.status}` : 'Connecting'}
        </div>
      </header>

      <section className="countryHero">
        <div>
          <div className="label">FIRST COUNTRY SLICE</div>
          <h2>Spain</h2>
          <p>
            Live local snapshot from AUGUR's analytical store, now enriched with
            multi-year trajectory analysis from the historical series.
          </p>
        </div>

        <div className="countryMeta">
          <div>
            <span>Indicators</span>
            <strong>{snapshot?.observation_count ?? '—'}</strong>
          </div>
          <div>
            <span>Country</span>
            <strong>ESP</strong>
          </div>
        </div>
      </section>

      {error && (
        <section className="error">
          AUGUR data connection failed: {error}
        </section>
      )}

      <section className="assessmentSection">
        <div className="dimensionHeader">
          <div>
            <div className="label">COUNTRY SIGNAL SUMMARY</div>
            <h3>Current trajectory by dimension</h3>
          </div>
          <span>transparent synthesis · no composite score</span>
        </div>

        <div className="assessmentGrid">
          {dimensionOrder.map((dimension) => {
            const item = assessment?.dimensions?.[dimension]
            if (!item) return null

            const improving = item.improving_signals.map((signal) => signal.name)
            const deteriorating = item.deteriorating_signals.map((signal) => signal.name)

            return (
              <article className="assessmentCard" key={dimension}>
                <div className="assessmentTop">
                  <span>{dimensionLabels[dimension] ?? dimension}</span>
                  <span>{item.confidence} confidence</span>
                </div>

                <div className={`assessmentTrajectory ${item.trajectory}`}>
                  {item.trajectory.replace('_', ' ')}
                </div>

                <div className="assessmentCoverage">
                  Directional coverage: {item.directional_indicator_count}/{item.indicator_count}
                </div>

                <div className="signalList">
                  {improving.length > 0 && (
                    <div>
                      <strong>Improving</strong>
                      <span>{improving.join(' · ')}</span>
                    </div>
                  )}

                  {deteriorating.length > 0 && (
                    <div>
                      <strong>Deteriorating</strong>
                      <span>{deteriorating.join(' · ')}</span>
                    </div>
                  )}

                  {improving.length === 0 && deteriorating.length === 0 && (
                    <div>
                      <strong>Interpretation</strong>
                      <span>Context-dependent signals; no automatic positive/negative verdict.</span>
                    </div>
                  )}
                </div>
              </article>
            )
          })}
        </div>
      </section>

      {dimensionOrder.map((dimension) => {
        const indicators = grouped[dimension] ?? []
        if (!indicators.length) return null

        return (
          <section className="dimensionSection" key={dimension}>
            <div className="dimensionHeader">
              <div>
                <div className="label">DIMENSION</div>
                <h3>{dimensionLabels[dimension] ?? dimension}</h3>
              </div>
              <span>{indicators.length} indicators</span>
            </div>

            <div className="indicatorGrid">
              {indicators.map((indicator) => (
                <article className="metricCard" key={indicator.indicator_id}>
                  <div className="metricTop">
                    <span className="metricName">{indicator.name}</span>
                    <span className="metricYear">{indicator.period}</span>
                  </div>

                  <div className="metricValue">
                    {formatValue(indicator.value, indicator.unit)}
                  </div>

                  <div className="trendBlock">
                    <div className={`trendState ${indicator.trend?.interpretation ?? ''}`}>
                      <span className="trendArrow">{trendSymbol(indicator.trend?.direction)}</span>
                      <span>{trendLabel(indicator.trend)}</span>
                      <small>{indicator.trend?.confidence ?? '—'} confidence</small>
                    </div>

                    {indicator.interpretation_policy === 'target_range' && (
                      <div className="targetRule">
                        <span>{targetStatusLabel(indicator.trend?.target_status)}</span>
                        <span>
                          target {indicator.target_min}–{indicator.target_max}
                        </span>
                      </div>
                    )}

                    <div className="trendChanges">
                      <span>1Y <strong>{changeLabel(indicator.trend?.pct_change_1y ?? null)}</strong></span>
                      <span>3Y <strong>{changeLabel(indicator.trend?.pct_change_3y ?? null)}</strong></span>
                      <span>5Y <strong>{changeLabel(indicator.trend?.pct_change_5y ?? null)}</strong></span>
                    </div>
                  </div>

                  <div className="sourceQuality">
                    <div>
                      <strong>{indicator.sourceQuality?.preferred_source_name ?? indicator.source_id.replace('_', ' ')}</strong>
                      <span>
                        preferred source · {indicator.sourceQuality?.preferred_period ?? indicator.period}
                      </span>
                    </div>

                    <div>
                      <strong>
                        {indicator.sourceQuality?.source_count === 2
                          ? 'Corroborated'
                          : indicator.sourceQuality?.source_count && indicator.sourceQuality.source_count > 2
                          ? `${indicator.sourceQuality.source_count} sources`
                          : 'Single source'}
                      </strong>
                      <span>
                        {indicator.sourceQuality?.disagreement_pct == null
                          ? 'no comparison available'
                          : `${indicator.sourceQuality.disagreement_pct.toFixed(2)}% disagreement`}
                      </span>
                    </div>
                  </div>

                  <div className="metricFooter">
                    <span>{indicator.source_id.replace('_', ' ')}</span>
                    <span>{indicator.indicator_id}</span>
                  </div>
                </article>
              ))}
            </div>
          </section>
        )
      })}

      <footer>
        AUGUR v0.1 · Phase 1 · Observed data + trend analysis
      </footer>
    </main>
  )
}
