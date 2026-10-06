import { useEffect, useMemo, useState } from 'react'
import ProfilePanel from './components/ProfilePanel'
import ComparePanel from './components/ComparePanel'
import CountrySelect from './components/CountrySelect'
import OverviewPage from './components/OverviewPage'
import IndicatorsPage from './components/IndicatorsPage'
import SkillsLanguagesPage from './components/SkillsLanguagesPage'
import FuturePathsPage from './components/FuturePathsPage'
import { countryRoute, compareRoute, dimensionRoute, useAugurRoute, type CountryView } from './lib/routing'

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

type Operability = {
  status: 'empty' | 'partial' | 'ready'
  ready: boolean
  analysis_ready: boolean
  ttv_temporal_model_ready: boolean
  blockers: string[]
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
  methodology_note?: string | null
  comparability_note?: string | null
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

type PersonalizedDimension = {
  dimension: string
  explicit_weight?: number | null
  utility: Record<string, number>
  construct_count: number
  method: string
}

type PersonalizedComparisonResponse = {
  status: 'ready' | 'weights_missing'
  countries: string[]
  weights: {
    explicit: Record<string, number>
    scale: [number, number]
    missing_means: string
  }
  normalization: {
    version: string
    scope: string
    utility_range: [number, number]
    contextual_indicators_excluded: boolean
    semantic_construct_version: string
    notes: string[]
  }
  dimensions: PersonalizedDimension[]
}

type OverviewSeriesPoint = {
  period: number
  value: number
}

type OverviewSeriesItem = {
  indicator_id: string
  name: string
  dimension: string
  unit: string
  source_id: string
  points: OverviewSeriesPoint[]
}

type OverviewSeriesResponse = {
  country_iso3: string
  series: OverviewSeriesItem[]
}


type CountryDataBundle = {
  snapshot?: Snapshot
  trends?: TrendsResponse
  sourceQuality?: SourceQualityResponse
  assessment?: AssessmentResponse
  trajectory?: TrajectoryResponse
  scenarios?: ScenarioResponse
  overviewSeries?: OverviewSeriesResponse
}

const countryDataCache = new Map<string, CountryDataBundle>()
const comparisonCache = new Map<string, ComparisonResponse>()

const API_BASE = 'http://127.0.0.1:8020'

const dimensionLabels: Record<string, string> = {
  prosperity: 'Prosperity',
  productive_capacity: 'Productive capacity',
  demography: 'Demography',
  human_systems: 'Human systems',
  housing: 'Housing',
  safety: 'Safety',
  environment: 'Environment',
  infrastructure: 'Infrastructure',
  fiscal: 'Fiscal sustainability',
  strategic_resilience: 'Strategic resilience',
}

function formatValue(value: number, unit: string) {
  if (unit === 'percent' || unit === 'percent_gdp') return `${value.toFixed(1)}%`
  if (unit === 'persons') return new Intl.NumberFormat('en-US', { maximumFractionDigits: 0 }).format(value)
  if (unit === 'per_100k_people') return `${value.toFixed(1)} /100k`
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
  const { route, navigate } = useAugurRoute()
  const [countries, setCountries] = useState<Country[]>([])
  const [selectedCountry, setSelectedCountry] = useState(
    route.kind === 'compare' ? 'ESP' : route.countryIso3,
  )
  const [health, setHealth] = useState<Health | null>(null)
  const [operability, setOperability] = useState<Operability | null>(null)
  const [snapshot, setSnapshot] = useState<Snapshot | null>(null)
  const [trends, setTrends] = useState<TrendsResponse | null>(null)
  const [sourceQuality, setSourceQuality] = useState<SourceQualityResponse | null>(null)
  const [assessment, setAssessment] = useState<AssessmentResponse | null>(null)
  const [trajectory, setTrajectory] = useState<TrajectoryResponse | null>(null)
  const [scenarios, setScenarios] = useState<ScenarioResponse | null>(null)
  const [overviewSeries, setOverviewSeries] = useState<OverviewSeriesResponse | null>(null)
  const [comparison, setComparison] = useState<ComparisonResponse | null>(null)
  const [personalizedComparison, setPersonalizedComparison] = useState<PersonalizedComparisonResponse | null>(null)
  const [compareCountries, setCompareCountries] = useState<string[]>(
    route.kind === 'compare' ? route.countries : ['IRL', 'ESP', 'PRT'],
  )
  const activeView = route.view
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    document.body.style.overflowY = activeView === 'overview' ? '' : 'auto'
    return () => {
      document.body.style.overflowY = ''
    }
  }, [activeView])

  useEffect(() => {
    if (route.kind === 'compare') {
      setCompareCountries(route.countries)
    } else {
      setSelectedCountry(route.countryIso3)
    }
  }, [route])

  useEffect(() => {
    const controller = new AbortController()
    const signal = controller.signal

    Promise.allSettled([
      fetchJson(`${API_BASE}/api/countries`, 'Countries', signal),
      fetchJson(`${API_BASE}/api/health`, 'Health', signal),
      fetchJson(`${API_BASE}/api/operability`, 'Operability', signal),
    ]).then((results) => {
      if (signal.aborted) return

      const [countriesResult, healthResult, operabilityResult] = results
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

      if (operabilityResult.status === 'fulfilled') {
        setOperability(operabilityResult.value)
      } else {
        failures.push(String(operabilityResult.reason))
      }

      if (failures.length) setError(failures.join(' · '))
    })

    return () => controller.abort()
  }, [])

  useEffect(() => {
    let controller: AbortController | null = null

    function refreshRuntimeState() {
      controller?.abort()
      controller = new AbortController()
      const signal = controller.signal

      Promise.allSettled([
        fetchJson(`${API_BASE}/api/health`, 'Health', signal),
        fetchJson(`${API_BASE}/api/operability`, 'Operability', signal),
      ]).then(([healthResult, operabilityResult]) => {
        if (signal.aborted) return

        if (healthResult.status === 'fulfilled') {
          setHealth(healthResult.value)
        }

        if (operabilityResult.status === 'fulfilled') {
          setOperability(operabilityResult.value)
        }
      })
    }

    function handleVisibilityChange() {
      if (document.visibilityState === 'visible') {
        refreshRuntimeState()
      }
    }

    window.addEventListener('focus', refreshRuntimeState)
    document.addEventListener('visibilitychange', handleVisibilityChange)

    return () => {
      controller?.abort()
      window.removeEventListener('focus', refreshRuntimeState)
      document.removeEventListener('visibilitychange', handleVisibilityChange)
    }
  }, [])

  useEffect(() => {
    const controller = new AbortController()
    const signal = controller.signal
    const query = compareCountries.join(',')
    const cached = comparisonCache.get(query)

    if (cached) {
      setComparison(cached)
      return () => controller.abort()
    }

    fetchJson(
      `${API_BASE}/api/compare?countries=${query}`,
      'Comparison',
      signal,
    )
      .then((data) => {
        if (signal.aborted) return
        const typed = data as ComparisonResponse
        comparisonCache.set(query, typed)
        setComparison(typed)
      })
      .catch((err) => {
        if ((err as Error).name !== 'AbortError') {
          setError(String(err))
        }
      })

    return () => controller.abort()
  }, [compareCountries])

  useEffect(() => {
    if (activeView !== 'compare') return

    const controller = new AbortController()
    const signal = controller.signal
    const query = compareCountries.join(',')

    fetchJson(
      `${API_BASE}/api/compare/personalized?countries=${query}`,
      'Personalized comparison',
      signal,
    )
      .then((data) => {
        if (signal.aborted) return
        setPersonalizedComparison(data as PersonalizedComparisonResponse)
      })
      .catch((err) => {
        if ((err as Error).name !== 'AbortError') {
          setPersonalizedComparison(null)
          setError(String(err))
        }
      })

    return () => controller.abort()
  }, [compareCountries, activeView])

  function updateCompareCountry(slot: number, iso3: string) {
    setCompareCountries((current) => {
      const next = [...current]
      const existingSlot = current.findIndex(
        (value, index) => index !== slot && value === iso3,
      )

      if (existingSlot >= 0) {
        next[existingSlot] = current[slot]
      }

      next[slot] = iso3

      if (route.kind === 'compare') {
        navigate(compareRoute(next), { replace: true })
      }

      return next
    })
  }

  function changeCountry(iso3: string) {
    setSelectedCountry(iso3)

    if (route.kind === 'country') {
      navigate(countryRoute(iso3, route.view))
    } else if (route.kind === 'dimension') {
      navigate(dimensionRoute(iso3, route.dimension))
    }
  }

  function navigateView(view: CountryView | 'compare') {
    if (view === 'compare') {
      navigate(compareRoute(compareCountries))
      return
    }

    navigate(countryRoute(selectedCountry, view))
  }

  useEffect(() => {
    if (activeView === 'compare') return

    const controller = new AbortController()
    const signal = controller.signal
    const cached = countryDataCache.get(selectedCountry) ?? {}

    setError(null)

    const needsOverview = activeView === 'overview'
    const needsIndicators = activeView === 'indicators' || activeView === 'dimension'
    const needsOutlook = activeView === 'outlook'

    const requiredKeys: Array<keyof CountryDataBundle> = ['snapshot']
    if (needsOverview) requiredKeys.push('trends', 'assessment', 'scenarios', 'overviewSeries')
    if (needsIndicators) requiredKeys.push('trends', 'sourceQuality', 'assessment', 'overviewSeries')
    if (needsOutlook) requiredKeys.push('trends', 'trajectory', 'scenarios')

    const setters: Record<keyof CountryDataBundle, (value: any) => void> = {
      snapshot: setSnapshot,
      trends: setTrends,
      sourceQuality: setSourceQuality,
      assessment: setAssessment,
      trajectory: setTrajectory,
      scenarios: setScenarios,
      overviewSeries: setOverviewSeries,
    }

    const labels: Record<keyof CountryDataBundle, string> = {
      snapshot: 'Snapshot',
      trends: 'Trends',
      sourceQuality: 'Source quality',
      assessment: 'Assessment',
      trajectory: 'Trajectory',
      scenarios: 'Scenarios',
      overviewSeries: 'Overview series',
    }

    const paths: Record<keyof CountryDataBundle, string> = {
      snapshot: 'snapshot',
      trends: 'trends',
      sourceQuality: 'source-quality',
      assessment: 'assessment',
      trajectory: 'trajectory',
      scenarios: 'scenarios',
      overviewSeries: 'overview-series',
    }

    for (const key of requiredKeys) {
      const cachedValue = cached[key]
      if (cachedValue) {
        setters[key](cachedValue)
      } else {
        setters[key](null)
      }
    }

    const missing = requiredKeys.filter((key) => !cached[key])
    if (!missing.length) {
      return () => controller.abort()
    }

    Promise.allSettled(
      missing.map((key) =>
        fetchJson(
          `${API_BASE}/api/countries/${selectedCountry}/${paths[key]}`,
          labels[key],
          signal,
        ).then((value) => ({ key, value })),
      ),
    ).then((results) => {
      if (signal.aborted) return

      const nextBundle: CountryDataBundle = {
        ...(countryDataCache.get(selectedCountry) ?? {}),
      }
      const failures: string[] = []

      for (const result of results) {
        if (result.status === 'fulfilled') {
          const { key, value } = result.value
          ;(nextBundle as Record<string, unknown>)[key] = value
          setters[key](value)
        } else {
          failures.push(String(result.reason))
        }
      }

      countryDataCache.set(selectedCountry, nextBundle)
      if (failures.length) setError(failures.join(' · '))
    })

    return () => controller.abort()
  }, [selectedCountry, activeView])

  const selectedCountryMeta = countries.find((country) => country.iso3 === selectedCountry)

  const enrichedIndicators = useMemo(() => {
    const trendById = new Map(
      (trends?.indicators ?? []).map((item) => [item.indicator_id, item]),
    )

    return (snapshot?.indicators ?? []).map((indicator) => {
      const trendItem = trendById.get(indicator.indicator_id)
      return {
        ...indicator,
        trend: trendItem?.trend,
        interpretation_policy: trendItem?.interpretation_policy,
        target_min: trendItem?.target_min,
        target_max: trendItem?.target_max,
        methodology_note: trendItem?.methodology_note,
        comparability_note: trendItem?.comparability_note,
      }
    })
  }, [snapshot, trends])

  return (
    <main className={`shell view-${activeView}`}>
      <header className="dashboardTopbar">
        <div className="brandCompact">
          <h1 className="brandMark">AUGUR</h1>
          <span className="brandSub">country trajectory & personal fit</span>
        </div>

        <div className="topbarCountry">
          <span>Country</span>
          <CountrySelect
            countries={countries}
            value={selectedCountry}
            onChange={changeCountry}
            ariaLabel="Select country"
            compact
          />
        </div>

        <nav className="viewNav topbarNav" aria-label="AUGUR views">
          {[
            ['overview', 'Overview'],
            ['indicators', 'Indicators'],
            ['outlook', 'Outlook'],
            ['compare', 'Compare'],
            ['profile', 'Profile'],
            ['skills', 'Skills & Languages'],
          ].map(([id, label]) => (
            <button
              key={id}
              type="button"
              className={activeView === id || (activeView === 'dimension' && id === 'indicators') ? 'active' : ''}
              onClick={() => navigateView(id as CountryView | 'compare')}
            >
              {label}
            </button>
          ))}
        </nav>

        <div className="topbarMeta">
          <div>
            <span>Indicators</span>
            <strong>{snapshot?.observation_count ?? '—'}</strong>
          </div>
          <div>
            <span>Country</span>
            <strong>{selectedCountry}</strong>
          </div>
          <div
            className={`status compact dataStatus ${
              operability
                ? operability.analysis_ready
                  ? 'ready'
                  : operability.status
                : 'connecting'
            }`}
            title={
              operability
                ? operability.blockers?.length
                  ? `Product: ${operability.status} · Blockers: ${operability.blockers.join(', ')}`
                  : `Product: ${operability.status} · analytical evidence ready`
                : 'Checking analytical evidence'
            }
          >
            <span className="dot" />
            {operability
              ? `Evidence · ${operability.analysis_ready ? 'ready' : operability.status}`
              : 'Evidence · checking'}
          </div>
          <div className={`status compact ${health?.status === 'ok' ? 'ok' : ''}`}>
            <span className="dot" />
            {health ? `P${health.phase} · ${health.status}` : 'Connecting'}
          </div>
        </div>
      </header>

      {error && (
        <section className="error">
          AUGUR data connection failed: {error}
        </section>
      )}

      {activeView === 'overview' && (
        <OverviewPage
          apiBase={API_BASE}
          countries={countries}
          selectedCountry={selectedCountry}
          selectedCountryName={selectedCountryMeta?.name ?? selectedCountry}
          selectedCountryIso2={selectedCountryMeta?.iso2 ?? ''}
          currentIndicators={enrichedIndicators}
          overviewSeries={overviewSeries?.series ?? []}
          assessment={assessment}
          scenarios={scenarios}
          compareCountries={compareCountries}
          comparison={comparison}
          onCountryChange={changeCountry}
          onCompareCountryChange={updateCompareCountry}
          onOpenOutlook={() => navigateView('outlook')}
          onOpenCompare={() => navigateView('compare')}
          onOpenIndicators={() => navigateView('indicators')}
          onOpenDimension={(dimension) => navigate(dimensionRoute(selectedCountry, dimension))}
          formatValue={formatValue}
          dimensionLabels={dimensionLabels}
        />
      )}

      {activeView === 'profile' && (
        <ProfilePanel apiBase={API_BASE} targetCountry={selectedCountry} />
      )}

      {activeView === 'skills' && (
        <SkillsLanguagesPage
          apiBase={API_BASE}
          targetCountry={selectedCountry}
          countryName={selectedCountryMeta?.name ?? selectedCountry}
        />
      )}

      {(activeView === 'indicators' || activeView === 'dimension') && (
        <IndicatorsPage
          countryName={selectedCountryMeta?.name ?? selectedCountry}
          indicators={enrichedIndicators}
          overviewSeries={overviewSeries?.series ?? []}
          sourceQuality={sourceQuality?.indicators ?? []}
          assessment={assessment?.dimensions}
          dimension={route.kind === 'dimension' ? route.dimension : null}
          dimensionLabels={dimensionLabels}
          formatValue={formatValue}
          onOpenDimension={(dimension) => navigate(dimensionRoute(selectedCountry, dimension))}
          onBackToIndicators={() => navigate(countryRoute(selectedCountry, 'indicators'))}
        />
      )}

      {activeView === 'outlook' && (
        <FuturePathsPage
          countryName={selectedCountryMeta?.name ?? selectedCountry}
          currentIndicators={enrichedIndicators}
          trajectory={trajectory}
          scenarios={scenarios}
          formatValue={formatValue}
        />
      )}

      {activeView === 'compare' && (
        <ComparePanel
          countries={countries}
          selected={compareCountries}
          onChange={updateCompareCountry}
          comparison={comparison}
          personalized={personalizedComparison}
          formatValue={formatValue}
          dimensionLabels={dimensionLabels}
        />
      )}

      <footer>
        AUGUR v0.1 · Phase 1 · country evidence + personal fit
      </footer>
    </main>
  )
}
