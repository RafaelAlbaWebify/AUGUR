import WorldMap from './WorldMap'
import './overview-page.css'

type Country = {
  iso2?: string
  iso3: string
  name: string
}

type Trend = {
  direction: string
  interpretation: string
  confidence: string
  pct_change_1y: number | null
  pct_change_3y: number | null
  pct_change_5y: number | null
}

type Indicator = {
  indicator_id: string
  name: string
  dimension: string
  period: number
  value: number
  unit: string
  source_id: string
  trend?: Trend
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
  dimensions: Record<string, DimensionAssessment>
}

type ScenarioIndicator = {
  name: string
  unit: string
  scenarios: {
    baseline: number
    improvement: number
    stress: number
  }
}

type ScenarioResponse = {
  indicators: ScenarioIndicator[]
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
  countries: Country[]
  indicator_count: number
  indicators: ComparisonIndicator[]
}

type OverviewPageProps = {
  apiBase: string
  countries: Country[]
  selectedCountry: string
  selectedCountryName: string
  currentIndicators: Indicator[]
  assessment: AssessmentResponse | null
  scenarios: ScenarioResponse | null
  compareCountries: string[]
  comparison: ComparisonResponse | null
  onCountryChange: (iso3: string) => void
  onCompareCountryChange: (slot: number, iso3: string) => void
  onOpenOutlook: () => void
  onOpenCompare: () => void
  onOpenDimension: (dimension: string) => void
  formatValue: (value: number, unit: string) => string
  dimensionLabels: Record<string, string>
}

const RADAR_DOMAINS = [
  { id: 'economy', label: 'Economy', dimension: 'prosperity', indicators: ['real_gdp_per_capita', 'real_gdp_growth', 'household_price_level_index'] },
  { id: 'labour', label: 'Labour market', dimension: 'productive_capacity', indicators: ['employment_rate_20_64', 'unemployment_rate', 'imf_unemployment_rate'] },
  { id: 'housing', label: 'Housing', dimension: 'housing', indicators: ['housing_cost_overburden_rate', 'real_house_price_index', 'rent_price_index'] },
  { id: 'healthcare', label: 'Healthcare', dimension: 'human_systems', indicators: ['life_expectancy'] },
  { id: 'safety', label: 'Safety', dimension: null, indicators: [] },
  { id: 'environment', label: 'Environment', dimension: null, indicators: [] },
  { id: 'infrastructure', label: 'Infrastructure', dimension: null, indicators: [] },
  { id: 'education', label: 'Education', dimension: 'human_systems', indicators: ['tertiary_education_25_34'] },
  { id: 'demography', label: 'Demography', dimension: 'demography', indicators: ['population_65_plus_share', 'fertility_rate', 'median_age'] },
  { id: 'resilience', label: 'Resilience', dimension: 'strategic_resilience', indicators: ['energy_import_dependency', 'public_debt_gdp'] },
] as const

function changeLabel(value: number | null | undefined) {
  if (value == null) return '—'
  const sign = value > 0 ? '+' : ''
  return `${sign}${value.toFixed(1)}%`
}

function trajectoryTone(value?: string) {
  if (value === 'improving') return 'good'
  if (value === 'deteriorating') return 'bad'
  if (value === 'mixed') return 'warn'
  return 'neutral'
}

export default function OverviewPage({
  countries,
  selectedCountry,
  selectedCountryName,
  currentIndicators,
  assessment,
  onCountryChange,
  onOpenDimension,
  formatValue,
  dimensionLabels,
}: OverviewPageProps) {
  const directional = Object.values(assessment?.dimensions ?? {}).reduce(
    (sum, item) => sum + item.directional_indicator_count,
    0,
  )
  const total = Object.values(assessment?.dimensions ?? {}).reduce(
    (sum, item) => sum + item.indicator_count,
    0,
  )

  const recentChanges = [...currentIndicators]
    .filter((item) => item.trend?.pct_change_1y != null && item.trend?.interpretation !== 'neutral_or_contextual')
    .sort((a, b) => Math.abs(b.trend?.pct_change_1y ?? 0) - Math.abs(a.trend?.pct_change_1y ?? 0))
    .slice(0, 4)

  const improvingSignals = Object.values(assessment?.dimensions ?? {})
    .flatMap((item) => item.improving_signals)
    .slice(0, 3)
  const pressureSignals = Object.values(assessment?.dimensions ?? {})
    .flatMap((item) => item.deteriorating_signals)
    .slice(0, 3)

  const representative = RADAR_DOMAINS.map((domain) => {
    const preferred = domain.indicators
      .map((indicatorId) => currentIndicators.find((item) => item.indicator_id === indicatorId))
      .find(Boolean)
      ?? (domain.dimension ? currentIndicators.find((item) => item.dimension === domain.dimension) : undefined)

    return {
      ...domain,
      item: preferred ?? null,
      assessment: domain.dimension ? assessment?.dimensions?.[domain.dimension] : undefined,
    }
  })

  return (
    <section className="countryRadarPage" aria-label="Country overview">
      <header className="countryRadarHeader">
        <div>
          <span>1. COUNTRY RADAR / Overview</span>
          <h2>{selectedCountryName} — country trajectory</h2>
        </div>
        <p>Key signals at a glance. No single composite score.</p>
      </header>

      <div className="countryRadarHero">
        <section className="countryIdentityCard">
          <div>
            <span>COUNTRY</span>
            <h3>{selectedCountryName}</h3>
            <strong>{selectedCountry}</strong>
          </div>
          <dl>
            <div><dt>Indicators loaded</dt><dd>{currentIndicators.length}</dd></div>
            <div><dt>Directional evidence</dt><dd>{directional} / {total || '—'}</dd></div>
            <div><dt>Dimensions assessed</dt><dd>{Object.keys(assessment?.dimensions ?? {}).length}</dd></div>
          </dl>
          <p>Country-level evidence. Regional/city insight appears only when a verified subnational source is available.</p>
        </section>

        <section className="countryRadarMap">
          <div className="radarPanelTopline">
            <div>
              <span>MAP</span>
              <strong>Registered country coverage</strong>
            </div>
            <span>Regional layer not yet implemented</span>
          </div>
          <WorldMap
            countries={countries}
            selectedCountry={selectedCountry}
            onSelectCountry={onCountryChange}
          />
        </section>

        <section className="recentChangesPanel">
          <div className="radarPanelTopline">
            <div><span>RECENT CHANGES</span><strong>Latest one-year movements</strong></div>
          </div>
          <div className="recentChangeList">
            {recentChanges.map((item) => (
              <article key={item.indicator_id} className={trajectoryTone(item.trend?.interpretation)}>
                <span className="changeArrow">{item.trend?.interpretation === 'improving' ? '↑' : item.trend?.interpretation === 'deteriorating' ? '↓' : '→'}</span>
                <div>
                  <strong>{item.name}</strong>
                  <small>{changeLabel(item.trend?.pct_change_1y)} · {item.period} · {item.source_id.replaceAll('_', ' ')}</small>
                </div>
              </article>
            ))}
            {!recentChanges.length && <span className="radarEmpty">No directional one-year changes available.</span>}
          </div>

          <div className="signalSplit">
            <div>
              <strong>Improving signals</strong>
              {improvingSignals.length
                ? improvingSignals.map((item) => <span key={item.indicator_id}>+ {item.name}</span>)
                : <span>None currently classified</span>}
            </div>
            <div>
              <strong>Key pressures</strong>
              {pressureSignals.length
                ? pressureSignals.map((item) => <span key={item.indicator_id}>− {item.name}</span>)
                : <span>None currently classified</span>}
            </div>
          </div>
        </section>
      </div>

      <section className="countryMetricGrid">
        {representative.map(({ id, label, dimension, item, assessment: dimensionState }) => (
          <button
            type="button"
            key={id}
            className={`countryMetricCard ${item ? trajectoryTone(dimensionState?.trajectory) : 'unavailable'}`}
            onClick={() => dimension && item ? onOpenDimension(dimension) : undefined}
            disabled={!dimension || !item}
          >
            <div className="countryMetricTop">
              <span>{label}</span>
              <small>{item ? (dimensionState?.trajectory?.replaceAll('_', ' ') ?? 'contextual') : 'evidence gap'}</small>
            </div>
            {item ? (
              <>
                <strong className="countryMetricName">{item.name}</strong>
                <div className="countryMetricValue">{formatValue(item.value, item.unit)}</div>
                <div className="countryMetricTrend">
                  <strong>{changeLabel(item.trend?.pct_change_1y)}</strong>
                  <span>1y · {item.trend?.confidence ?? 'evidence pending'} evidence</span>
                </div>
                <div className="countryMetricFooter">
                  <span>{item.source_id.replaceAll('_', ' ')}</span>
                  <span>{item.period}</span>
                </div>
              </>
            ) : (
              <>
                <strong className="countryMetricName">No verified indicator integrated yet</strong>
                <div className="countryMetricValue unavailableValue">—</div>
                <div className="countryMetricTrend">
                  <strong>Evidence unavailable</strong>
                  <span>Shown deliberately so the coverage gap is visible.</span>
                </div>
                <div className="countryMetricFooter">
                  <span>Pending source integration</span>
                </div>
              </>
            )}
          </button>
        ))}
      </section>

      <section className="countryRadarFooter">
        <div>
          <span>WHAT THIS VIEW MEANS</span>
          <strong>Level + direction + evidence, not a universal ranking</strong>
        </div>
        <p>
          Open any domain to inspect the contributing indicators, source quality and disagreements before treating a trajectory as decision evidence.
        </p>
      </section>
    </section>
  )
}
