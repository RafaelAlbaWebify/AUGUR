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

const API_BASE = 'http://127.0.0.1:8020'

const dimensionOrder = [
  'prosperity',
  'productive_capacity',
  'demography',
]

const dimensionLabels: Record<string, string> = {
  prosperity: 'Prosperity',
  productive_capacity: 'Productive capacity',
  demography: 'Demography',
}

function formatValue(value: number, unit: string) {
  if (unit === 'percent') return `${value.toFixed(1)}%`
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
  if (trend.direction === 'stable') return 'Stable'
  return 'Contextual'
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
    ])
      .then(([healthData, snapshotData, trendsData]) => {
        setHealth(healthData)
        setSnapshot(snapshotData)
        setTrends(trendsData)
      })
      .catch((err) => setError(String(err)))
  }, [])

  const grouped = useMemo(() => {
    const groups: Record<string, Indicator[]> = {}
    const trendById = new Map((trends?.indicators ?? []).map((item) => [item.indicator_id, item.trend]))

    for (const indicator of snapshot?.indicators ?? []) {
      const enriched = {
        ...indicator,
        trend: trendById.get(indicator.indicator_id),
      }
      groups[indicator.dimension] ??= []
      groups[indicator.dimension].push(enriched)
    }

    return groups
  }, [snapshot, trends])

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
                    <div className="trendChanges">
                      <span>1Y <strong>{changeLabel(indicator.trend?.pct_change_1y ?? null)}</strong></span>
                      <span>3Y <strong>{changeLabel(indicator.trend?.pct_change_3y ?? null)}</strong></span>
                      <span>5Y <strong>{changeLabel(indicator.trend?.pct_change_5y ?? null)}</strong></span>
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
