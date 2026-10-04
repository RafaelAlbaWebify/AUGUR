import { useEffect, useState } from 'react'
import RegionalMap from './RegionalMap'
import { countryVisual } from '../lib/countryVisuals'
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

type OverviewSeriesItem = {
  indicator_id: string
  name: string
  dimension: string
  unit: string
  source_id: string
  points: Array<{ period: number; value: number }>
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
  selectedCountryIso2: string
  currentIndicators: Indicator[]
  overviewSeries: OverviewSeriesItem[]
  assessment: AssessmentResponse | null
  scenarios: ScenarioResponse | null
  compareCountries: string[]
  comparison: ComparisonResponse | null
  onCountryChange: (iso3: string) => void
  onCompareCountryChange: (slot: number, iso3: string) => void
  onOpenOutlook: () => void
  onOpenCompare: () => void
  onOpenIndicators: () => void
  onOpenDimension: (dimension: string) => void
  formatValue: (value: number, unit: string) => string
  dimensionLabels: Record<string, string>
}

const RADAR_DOMAINS = [
  { id: 'economy', label: 'Economy', dimension: 'prosperity', indicators: ['actual_individual_consumption_index', 'real_gdp_per_capita', 'real_gdp_growth', 'household_price_level_index'] },
  { id: 'labour', label: 'Labour market', dimension: 'productive_capacity', indicators: ['employment_rate_20_64', 'unemployment_rate', 'imf_unemployment_rate'] },
  { id: 'housing', label: 'Housing', dimension: 'housing', indicators: ['housing_cost_overburden_rate', 'real_house_price_index', 'rent_price_index'] },
  { id: 'healthcare', label: 'Healthcare', dimension: 'human_systems', indicators: ['life_expectancy'] },
  { id: 'safety', label: 'Safety', dimension: 'safety', indicators: ['intentional_homicide_rate'] },
  { id: 'environment', label: 'Environment', dimension: 'environment', indicators: ['pm25_premature_death_rate'] },
  { id: 'infrastructure', label: 'Infrastructure', dimension: 'infrastructure', indicators: ['household_internet_access'] },
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


const DOMAIN_ICONS: Record<string, string> = {
  economy: '€',
  labour: '◉',
  housing: '⌂',
  healthcare: '✚',
  safety: '◇',
  environment: '●',
  infrastructure: '▦',
  education: '◆',
  demography: '◌',
  resilience: '⬟',
}

function selectedSetBand(
  comparison: ComparisonResponse | null,
  indicatorId: string,
  selectedCountry: string,
) {
  const row = comparison?.indicators.find((item) => item.indicator_id === indicatorId)
  if (!row) return null

  const entries = Object.entries(row.countries)
    .filter(([, item]) => typeof item?.value === 'number')
    .sort((a, b) => a[1].value - b[1].value)

  if (entries.length < 2) return null

  const index = entries.findIndex(([iso3]) => iso3 === selectedCountry)
  if (index < 0) return null
  if (index === 0) return 'Low in selected set'
  if (index === entries.length - 1) return 'High in selected set'
  return 'Mid in selected set'
}

function sparklinePoints(points: Array<{ period: number; value: number }>) {
  if (points.length < 2) return ''
  const width = 112
  const height = 42
  const pad = 3
  const values = points.map((point) => point.value)
  const min = Math.min(...values)
  const max = Math.max(...values)
  const range = Math.max(1e-9, max - min)

  return points.map((point, index) => {
    const x = pad + (index / (points.length - 1)) * (width - pad * 2)
    const y = pad + (1 - ((point.value - min) / range)) * (height - pad * 2)
    return `${x.toFixed(1)},${y.toFixed(1)}`
  }).join(' ')
}

export default function OverviewPage({
  countries,
  selectedCountry,
  selectedCountryName,
  selectedCountryIso2,
  currentIndicators,
  overviewSeries,
  assessment,
  comparison,
  onCountryChange,
  onOpenIndicators,
  onOpenDimension,
  formatValue,
  dimensionLabels,
}: OverviewPageProps) {
  const [mapMode, setMapMode] = useState<'map' | 'regions'>('map')
  const [selectedRegion, setSelectedRegion] = useState<{ id: string; name: string } | null>(null)

  useEffect(() => {
    setSelectedRegion(null)
  }, [selectedCountry])

  const visual = countryVisual(selectedCountry)

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

  const seriesById = new Map(overviewSeries.map((item) => [item.indicator_id, item]))

  const representative = RADAR_DOMAINS.map((domain) => {
    const preferred = domain.indicators
      .map((indicatorId) => currentIndicators.find((item) => item.indicator_id === indicatorId))
      .find(Boolean)
      ?? (domain.dimension ? currentIndicators.find((item) => item.dimension === domain.dimension) : undefined)

    return {
      ...domain,
      item: preferred ?? null,
      assessment: preferred ? assessment?.dimensions?.[preferred.dimension] : undefined,
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
          <img
            className="countryHeroImage"
            src={visual.heroImage}
            alt={visual.alt}
            style={{ objectPosition: visual.focalPoint }}
            onError={(event) => {
              const image = event.currentTarget
              if (image.src.endsWith(visual.fallbackImage)) return
              image.src = visual.fallbackImage
            }}
          />
          <div className="countryHeroOverlay" aria-hidden="true" />

          <div className="countryHeroMeta">
            <span>{selectedCountry}</span>
            <span>{currentIndicators.length} indicators</span>
            <span>{directional}/{total || '—'} directional</span>
          </div>

          <div className="countryHeroBottom">
            {selectedRegion && (
              <span className="countryRegionFocus">REGION · {selectedRegion.name} · {selectedRegion.id}</span>
            )}
            <h3>{selectedCountryName.toUpperCase()}</h3>
            <p>{visual.summary ?? 'Country evidence is active. Regional metrics appear only where verified subnational sources exist.'}</p>
          </div>
        </section>

        <section className="countryRadarMap">
          <div className="radarPanelTopline mapPanelHeader">
            <div>
              <span>MAP</span>
              <strong>{mapMode === 'regions' ? 'Region directory' : 'Selectable NUTS 2 map'}</strong>
            </div>
            <div className="mapModeToggle" role="group" aria-label="Map layer">
              <button
                type="button"
                className={mapMode === 'map' ? 'active' : ''}
                onClick={() => setMapMode('map')}
              >
                Map
              </button>
              <button
                type="button"
                className={mapMode === 'regions' ? 'active' : ''}
                onClick={() => setMapMode('regions')}
              >
                Regions
              </button>
            </div>
          </div>

          {selectedCountryIso2 ? (
            <RegionalMap
              countryIso2={selectedCountryIso2}
              selectedRegion={selectedRegion?.id ?? null}
              onSelectRegion={(id, name) => setSelectedRegion({ id, name })}
              cities={visual.cities}
              showRegionList={mapMode === 'regions'}
            />
          ) : (
            <div className="regionalMapState error">Regional map unavailable for this country.</div>
          )}
        </section>

        <section className="recentChangesPanel">
          <div className="radarPanelTopline">
            <div><span>RECENT CHANGES (12 MONTHS)</span><strong>Largest measured movements</strong></div>
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

          <button type="button" className="viewAllChanges" onClick={onOpenIndicators}>
            View all changes →
          </button>

          <div className="signalSplit">
            <div>
              <strong>Strengths / improving evidence</strong>
              {improvingSignals.length
                ? improvingSignals.map((item) => <span key={item.indicator_id}>+ {item.name}</span>)
                : <span>None currently classified</span>}
            </div>
            <div>
              <strong>Key risks / deteriorating evidence</strong>
              {pressureSignals.length
                ? pressureSignals.map((item) => <span key={item.indicator_id}>− {item.name}</span>)
                : <span>None currently classified</span>}
            </div>
          </div>
        </section>
      </div>

      {selectedRegion && (
        <div className="regionalFocusNotice">
          <strong>{selectedRegion.name} selected</strong>
          <span>
            Map focus is regional · domain cards remain national evidence until a verified regional series is available.
          </span>
        </div>
      )}

      <section className="countryMetricGrid">
        {representative.map(({ id, label, dimension, item, assessment: dimensionState }) => (
          <button
            type="button"
            key={id}
            className={`countryMetricCard ${item ? trajectoryTone(dimensionState?.trajectory) : 'unavailable'}`}
            onClick={() => item ? onOpenDimension(item.dimension) : undefined}
            disabled={!item}
          >
            <div className="countryMetricTop">
              <span>{label}</span>
              <small>{item ? (dimensionState?.trajectory?.replaceAll('_', ' ') ?? 'contextual') : 'evidence gap'}</small>
            </div>
            {item ? (
              <>
                <div className="countryMetricIdentity">
                  <span className={`countryMetricIcon ${trajectoryTone(dimensionState?.trajectory)}`}>
                    {DOMAIN_ICONS[id] ?? '•'}
                  </span>
                  <strong className="countryMetricName">{item.name}</strong>
                </div>

                <div className="countryMetricEvidenceRow">
                  <div>
                    <div className="countryMetricValue">{formatValue(item.value, item.unit)}</div>
                    <div className="countryMetricTrend">
                      <strong>{changeLabel(item.trend?.pct_change_1y)}</strong>
                      <span>vs. previous year</span>
                    </div>
                  </div>

                  <div className="countryMetricSparkline" aria-label={`${item.name} recent history`}>
                    {seriesById.get(item.indicator_id)?.points?.length && seriesById.get(item.indicator_id)!.points.length >= 2 ? (
                      <svg viewBox="0 0 112 42" role="img">
                        <polyline points={sparklinePoints(seriesById.get(item.indicator_id)!.points)} />
                        {seriesById.get(item.indicator_id)!.points.map((point, pointIndex, allPoints) => {
                          const coordinates = sparklinePoints(allPoints).split(' ')[pointIndex]?.split(',') ?? ['0', '0']
                          return <circle key={point.period} cx={coordinates[0]} cy={coordinates[1]} r={pointIndex === allPoints.length - 1 ? 2.8 : 1.6} />
                        })}
                      </svg>
                    ) : (
                      <span>history unavailable</span>
                    )}
                  </div>
                </div>

                <div className="countryMetricFooter">
                  <span className="countryMetricPeerBadge">
                    {selectedSetBand(comparison, item.indicator_id, selectedCountry) ?? 'Peer reference pending'}
                  </span>
                  <span>{item.source_id.replaceAll('_', ' ')} · {item.period}</span>
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
