import { useEffect, useMemo, useState } from 'react'
import WorldMap from './components/WorldMap'
import ProfilePanel from './components/ProfilePanel'

type Country = {
  iso2: string
  iso3: string
  name: string
  region: string
  subregion: string
  currency: string
  eu_member: boolean
  eurozone_member: boolean
  oecd_member: boolean
}

type CountriesResponse = {
  countries: Country[]
}

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
  evidence_status?: string
  evidence_note?: string | null
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
  common_period: number | null
  common_period_source_count: number | null
  disagreement_pct: number | null
}

type SourceQualityResponse = {
  country_iso3: string
  indicators: SourceQualityItem[]
}

type TrajectoryIndicator = {
  country_iso3: string
  indicator_id: string
  name: string
  dimension: string
  period: number
  value: number
  unit: string
  source_id: string
  source_name: string
  dataset_id: string
  observation_type: string
  source_updated_at?: string | null
}

type TrajectoryHorizon = {
  year: number
  indicator_count: number
  sources: string[]
  indicators: TrajectoryIndicator[]
}

type TrajectoryResponse = {
  country_iso3: string
  method: string
  horizons: TrajectoryHorizon[]
  notes: string[]
}

type ScenarioIndicator = TrajectoryIndicator & {
  official_baseline: number
  scenarios: {
    baseline: number
    improvement: number
    stress: number
  }
  assumption: string
  uncertainty: {
    multiplier: number
    level: string
  }
}

type ScenarioResponse = {
  country_iso3: string
  method: string
  horizons: number[]
  scenario_names: string[]
  indicators: ScenarioIndicator[]
  notes: string[]
}

type ComparisonCountryValue = {
  period: number
  value: number
  source_id: string
}

type ComparisonIndicator = {
  indicator_id: string
  name: string
  dimension: string
  unit: string
  countries: Record<string, ComparisonCountryValue>
}

type ComparisonResponse = {
  countries: Array<{ iso3: string; name: string }>
  indicator_count: number
  indicators: ComparisonIndicator[]
  method: string
  notes: string[]
}

const API_BASE = 'http://127.0.0.1:8020'

const dimensionOrder = [
  'prosperity',
  'productive_capacity',
  'housing',
  'demography',
  'human_systems',
  'fiscal',
  'strategic_resilience',
]

const dimensionLabels: Record<string, string> = {
  prosperity: 'Prosperity',
  productive_capacity: 'Productive capacity',
  demography: 'Demography',
  human_systems: 'Human systems',
  housing: 'Housing',
  fiscal: 'Fiscal sustainability',
  strategic_resilience: 'Strategic resilience',
}

function formatValue(value: number, unit: string) {
  if (unit === 'percent' || unit === 'percent_gdp') return `${value.toFixed(1)}%`
  if (unit === 'persons') return new Intl.NumberFormat('en-US', { maximumFractionDigits: 0 }).format(value)
  if (unit === 'births_per_woman') return value.toFixed(2)
  if (unit === 'years') return `${value.toFixed(1)} years`
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
  if (unit === 'index_eu27_2020_100') {
    return `${value.toFixed(1)} · EU=100`
  }
  if (unit === 'index_2015_100') {
    return `${value.toFixed(1)} · 2015=100`
  }
  if (unit === 'index_annual_average') {
    return value.toFixed(1)
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

async function fetchJson(
  url: string,
  label: string,
  signal: AbortSignal,
) {
  const response = await fetch(url, { signal })
  if (!response.ok) throw new Error(`${label} HTTP ${response.status}`)
  return response.json()
}

export default function App() {
  const [countries, setCountries] = useState<Country[]>([])
  const [selectedCountry, setSelectedCountry] = useState('ESP')
  const [health, setHealth] = useState<Health | null>(null)
  const [snapshot, setSnapshot] = useState<Snapshot | null>(null)
  const [trends, setTrends] = useState<TrendsResponse | null>(null)
  const [assessment, setAssessment] = useState<AssessmentResponse | null>(null)
  const [sourceQuality, setSourceQuality] = useState<SourceQualityResponse | null>(null)
  const [trajectory, setTrajectory] = useState<TrajectoryResponse | null>(null)
  const [scenarios, setScenarios] = useState<ScenarioResponse | null>(null)
  const [comparison, setComparison] = useState<ComparisonResponse | null>(null)
  const [activeView, setActiveView] = useState<'overview' | 'outlook' | 'compare' | 'profile'>('overview')
  const [detailsExpanded, setDetailsExpanded] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const controller = new AbortController()
    const signal = controller.signal

    Promise.allSettled([
      fetchJson(`${API_BASE}/api/countries`, 'Countries', signal),
      fetchJson(`${API_BASE}/api/health`, 'Health', signal),
      fetchJson(`${API_BASE}/api/compare?countries=ESP,PRT,IRL`, 'Comparison', signal),
    ]).then((results) => {
      if (signal.aborted) return

      const [countriesResult, healthResult, comparisonResult] = results
      const failures: string[] = []

      if (countriesResult.status === 'fulfilled') {
        setCountries((countriesResult.value as CountriesResponse).countries)
      } else {
        failures.push(String(countriesResult.reason))
      }

      if (healthResult.status === 'fulfilled') {
        setHealth(healthResult.value)
      } else {
        failures.push(String(healthResult.reason))
      }

      if (comparisonResult.status === 'fulfilled') {
        setComparison(comparisonResult.value)
      } else {
        failures.push(String(comparisonResult.reason))
      }

      if (failures.length) setError(failures.join(' · '))
    })

    return () => controller.abort()
  }, [])

  useEffect(() => {
    const controller = new AbortController()
    const signal = controller.signal

    setError(null)
    setSnapshot(null)
    setTrends(null)
    setAssessment(null)
    setSourceQuality(null)
    setTrajectory(null)
    setScenarios(null)

    Promise.allSettled([
      fetchJson(`${API_BASE}/api/countries/${selectedCountry}/snapshot`, 'Snapshot', signal),
      fetchJson(`${API_BASE}/api/countries/${selectedCountry}/trends`, 'Trends', signal),
      fetchJson(`${API_BASE}/api/countries/${selectedCountry}/assessment`, 'Assessment', signal),
      fetchJson(`${API_BASE}/api/countries/${selectedCountry}/source-quality`, 'Source quality', signal),
      fetchJson(`${API_BASE}/api/countries/${selectedCountry}/trajectory`, 'Trajectory', signal),
      fetchJson(`${API_BASE}/api/countries/${selectedCountry}/scenarios`, 'Scenarios', signal),
    ]).then((results) => {
      if (signal.aborted) return

      const [
        snapshotResult,
        trendsResult,
        assessmentResult,
        sourceQualityResult,
        trajectoryResult,
        scenariosResult,
      ] = results

      const failures: string[] = []

      if (snapshotResult.status === 'fulfilled') setSnapshot(snapshotResult.value)
      else failures.push(String(snapshotResult.reason))

      if (trendsResult.status === 'fulfilled') setTrends(trendsResult.value)
      else failures.push(String(trendsResult.reason))

      if (assessmentResult.status === 'fulfilled') setAssessment(assessmentResult.value)
      else failures.push(String(assessmentResult.reason))

      if (sourceQualityResult.status === 'fulfilled') setSourceQuality(sourceQualityResult.value)
      else failures.push(String(sourceQualityResult.reason))

      if (trajectoryResult.status === 'fulfilled') setTrajectory(trajectoryResult.value)
      else failures.push(String(trajectoryResult.reason))

      if (scenariosResult.status === 'fulfilled') setScenarios(scenariosResult.value)
      else failures.push(String(scenariosResult.reason))

      if (failures.length) setError(failures.join(' · '))
    })

    return () => controller.abort()
  }, [selectedCountry])

  const selectedCountryMeta = countries.find((country) => country.iso3 === selectedCountry)

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
          <div className="label">COUNTRY</div>
          <div className="countryTitleRow">
            <h2>{selectedCountryMeta?.name ?? selectedCountry}</h2>
            <select
              className="countrySelect"
              value={selectedCountry}
              onChange={(event) => setSelectedCountry(event.target.value)}
              aria-label="Select country"
            >
              {countries.map((country) => (
                <option value={country.iso3} key={country.iso3}>
                  {country.name}
                </option>
              ))}
            </select>
          </div>
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
            <strong>{selectedCountry}</strong>
          </div>
        </div>
      </section>

      {error && (
        <section className="error">
          AUGUR data connection failed: {error}
        </section>
      )}

      <nav className="viewNav" aria-label="AUGUR views">
        {[
          ['overview', 'Overview'],
          ['outlook', 'Outlook'],
          ['compare', 'Compare'],
          ['profile', 'Profile'],
        ].map(([id, label]) => (
          <button
            key={id}
            type="button"
            className={activeView === id ? 'active' : ''}
            onClick={() => setActiveView(id as 'overview' | 'outlook' | 'compare' | 'profile')}
          >
            {label}
          </button>
        ))}
      </nav>

      {activeView === 'overview' && (
        <WorldMap
          countries={countries}
          selectedCountry={selectedCountry}
          onSelectCountry={setSelectedCountry}
        />
      )}

      {activeView === 'profile' && (
        <ProfilePanel apiBase={API_BASE} targetCountry={selectedCountry} />
      )}

      {activeView === 'overview' && (
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
                  {item.evidence_status === 'limited' && (
                    <span className="assessmentEvidenceNote">
                      Broad verdict withheld · only one directional signal
                    </span>
                  )}
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
      )}

      {activeView === 'overview' && (
        <div className="detailsToggleRow">
          <button
            type="button"
            className="detailsToggle"
            onClick={() => setDetailsExpanded((value) => !value)}
          >
            {detailsExpanded ? 'Hide indicator details' : 'Show indicator details'}
          </button>
          <span>{snapshot?.observation_count ?? 0} current indicators</span>
        </div>
      )}

      {activeView === 'outlook' && (
      <section className="trajectorySection">
        <div className="dimensionHeader">
          <div>
            <div className="label">OFFICIAL OUTLOOK</div>
            <h3>2030 · 2035 · 2045</h3>
          </div>
          <span>official forecasts/projections · not an AUGUR prediction</span>
        </div>

        <div className="trajectoryGrid">
          {(trajectory?.horizons ?? []).map((horizon) => (
            <article className="trajectoryCard" key={horizon.year}>
              <div className="trajectoryYear">{horizon.year}</div>
              <div className="trajectorySources">
                {horizon.sources.length ? horizon.sources.join(' · ') : 'No official coverage'}
              </div>

              <div className="trajectoryIndicators">
                {horizon.indicators.length === 0 && (
                  <div className="trajectoryEmpty">No official forecast loaded for this horizon.</div>
                )}

                {horizon.indicators.map((item) => (
                  <div className="trajectoryRow" key={`${horizon.year}-${item.indicator_id}-${item.source_id}`}>
                    <span>{item.name}</span>
                    <strong>{formatValue(item.value, item.unit)}</strong>
                    <small>{item.source_name}</small>
                  </div>
                ))}
              </div>
            </article>
          ))}
        </div>
      </section>
      )}

      {activeView === 'outlook' && (
      <section className="scenarioSection">
        <div className="dimensionHeader">
          <div>
            <div className="label">AUGUR SCENARIOS</div>
            <h3>Baseline · Improvement · Stress</h3>
          </div>
          <span>baseline = official · alternatives = model assumptions</span>
        </div>

        <div className="scenarioGrid">
          {(scenarios?.horizons ?? []).map((year) => {
            const items = scenarios?.indicators.filter((item) => item.period === year) ?? []

            return (
              <article className="scenarioCard" key={year}>
                <div className="scenarioYearHeader">
                  <div className="trajectoryYear">{year}</div>
                  <div className="uncertaintyBadge">
                    {items[0]
                      ? `${items[0].uncertainty.level} uncertainty · ×${items[0].uncertainty.multiplier}`
                      : 'uncertainty unavailable'}
                  </div>
                </div>

                <div className="scenarioRows">
                  {items.map((item) => (
                    <div className="scenarioRow" key={`${year}-${item.indicator_id}-${item.source_id}`}>
                      <div className="scenarioName">{item.name}</div>
                      <div className="scenarioValues">
                        <span>
                          <small>Baseline</small>
                          <strong>{formatValue(item.scenarios.baseline, item.unit)}</strong>
                        </span>
                        <span>
                          <small>Improvement</small>
                          <strong>{formatValue(item.scenarios.improvement, item.unit)}</strong>
                        </span>
                        <span>
                          <small>Stress</small>
                          <strong>{formatValue(item.scenarios.stress, item.unit)}</strong>
                        </span>
                      </div>
                      <div className="scenarioAssumption">{item.assumption}</div>
                    </div>
                  ))}

                  {items.length === 0 && (
                    <div className="trajectoryEmpty">No scenario inputs available for this horizon.</div>
                  )}
                </div>
              </article>
            )
          })}
        </div>
      </section>
      )}

      {activeView === 'compare' && (
      <section className="comparisonSection">
        <div className="dimensionHeader">
          <div>
            <div className="label">COUNTRY COMPARISON</div>
            <h3>Spain · Portugal · Ireland</h3>
          </div>
          <span>aligned indicators · no ranking</span>
        </div>

        <div className="comparisonTableWrap">
          <table className="comparisonTable">
            <thead>
              <tr>
                <th>Indicator</th>
                {(comparison?.countries ?? []).map((country) => (
                  <th key={country.iso3}>{country.name}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {(comparison?.indicators ?? []).map((item) => (
                <tr key={item.indicator_id}>
                  <td>
                    <strong>{item.name}</strong>
                    <small>{dimensionLabels[item.dimension] ?? item.dimension}</small>
                  </td>

                  {(comparison?.countries ?? []).map((country) => {
                    const value = item.countries[country.iso3]
                    return (
                      <td key={country.iso3}>
                        {value ? (
                          <>
                            <strong>{formatValue(value.value, item.unit)}</strong>
                            <small>{value.period} · {value.source_id.replace('_', ' ')}</small>
                          </>
                        ) : (
                          <span className="comparisonMissing">—</span>
                        )}
                      </td>
                    )
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
      )}

      {activeView === 'overview' && detailsExpanded && dimensionOrder.map((dimension) => {
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
                          ? 'no same-period comparison'
                          : `${indicator.sourceQuality.disagreement_pct.toFixed(2)}% disagreement · ${indicator.sourceQuality.common_period}`}
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
