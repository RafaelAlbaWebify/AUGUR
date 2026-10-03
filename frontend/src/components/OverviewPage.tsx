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

const DIMENSION_ORDER = [
  'prosperity',
  'productive_capacity',
  'housing',
  'human_systems',
  'demography',
  'fiscal',
  'strategic_resilience',
]

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

  const representative = DIMENSION_ORDER.map((dimension) => {
    const candidates = currentIndicators.filter((item) => item.dimension === dimension)
    const preferred = candidates.find((item) => item.trend?.interpretation === 'improving' || item.trend?.interpretation === 'deteriorating')
      ?? candidates[0]
    return preferred ? { dimension, item: preferred } : null
  }).filter((entry): entry is { dimension: string; item: Indicator } => Boolean(entry))

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
        {representative.map(({ dimension, item }) => {
          const dimensionState = assessment?.dimensions?.[dimension]
          return (
            <button
              type="button"
              key={dimension}
              className={`countryMetricCard ${trajectoryTone(dimensionState?.trajectory)}`}
              onClick={() => onOpenDimension(dimension)}
            >
              <div className="countryMetricTop">
                <span>{dimensionLabels[dimension] ?? dimension}</span>
                <small>{dimensionState?.trajectory?.replaceAll('_', ' ') ?? 'contextual'}</small>
              </div>
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
            </button>
          )
        })}
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
