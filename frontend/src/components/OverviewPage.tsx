import { useEffect, useState } from 'react'
import RegionalMap from './RegionalMap'
import { countryVisual } from '../lib/countryVisuals'
import './overview-page.css'

type Country = {
  iso2?: string
  iso3: string
  name: string
}

type PeerReference = {
  status: string
  reference_group: string
  reference_countries: string[]
  sample_size: number
  period: number | null
  rank_low_to_high: number | null
  percentile_low_to_high: number | null
  adequacy: string
  interpretation: string
  note: string
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
  peer_reference?: PeerReference
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

type RegionalIndicator = {
  indicator_id: string
  name: string
  status: 'available' | 'unavailable'
  period?: number
  value?: number
  unit?: string
  dataset_id: string
  source_id: string
  reason?: string
  category?: string
  history?: Array<{ period: number; value: number }>
}

type RegionalSector = {
  nace_code: string
  nace_label?: string | null
  period: number
  employment_thousands: number
  employment_share_pct?: number | null
}

type EnvironmentalHealthMetric = {
  burden_type: string
  label: string
  period: number
  value: number
  unit_code: string
  unit_label: string
  obs_status?: string | null
}


type RegionalEvidenceResponse = {
  geo_code: string
  geo_level: string
  source: string
  indicator_count: number
  available_count: number
  complete: boolean
  indicators: RegionalIndicator[]
  sector_structure?: {
    status: string
    dataset_id: string
    source_id: string
    period?: number
    total_employment_thousands?: number | null
    sector_count?: number
    top_sectors?: RegionalSector[]
    notes?: string[]
  }
  environmental_health?: {
    status: string
    source_id: string
    dataset_id: string
    dataset_version?: string
    geo_level?: string
    period?: number
    comparison_policy?: {
      safe_for_direct_cross_region_comparison?: boolean
      reason?: string
      preferred_comparison_basis?: string
    }
    metrics?: EnvironmentalHealthMetric[]
    notes?: string[]
  }
  notes: string[]
}

type CountryGeography = {
  geo_id: string
  country_iso3: string
  country_iso2?: string | null
  name?: string | null
  geo_level: string
  geography_system: string
  source_id?: string | null
  source_geo_code: string
  parent_geo_id?: string | null
  latitude?: number | null
  longitude?: number | null
  indicator_count: number
  latest_period?: number | null
}

type GeographyResponse = {
  country_iso3: string
  geo_level?: string | null
  geographies: CountryGeography[]
}

type GeographyComparisonIndicator = {
  indicator_id: string
  name: string
  unit?: string | null
  regions: Record<string, RegionalIndicator>
}

type GeographyComparisonResponse = {
  geography_system: string
  geo_level: string
  regions: Array<{
    geo_code: string
    geo_name?: string | null
    geo_level: string
    source?: string
    source_ids?: string[]
  }>
  indicator_count: number
  indicators: GeographyComparisonIndicator[]
  notes?: string[]
}

type CityEvidenceResponse = {
  city_code: string
  geo_level: string
  source: string
  minimum_population_scope: number
  indicator_count: number
  available_count: number
  complete: boolean
  indicators: RegionalIndicator[]
  notes?: string[]
}

const regionalEvidenceCache = new Map<string, RegionalEvidenceResponse>()
const cityEvidenceCache = new Map<string, CityEvidenceResponse>()
const geographyCatalogCache = new Map<string, CountryGeography[]>()
const geographyComparisonCache = new Map<string, GeographyComparisonResponse>()

type OverviewPageProps = {
  apiBase: string
  countries: Country[]
  selectedCountry: string
  selectedCountryName: string
  selectedCountryIso2: string
  selectedCountryCenter: { lat: number; lon: number } | null
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
  { id: 'healthcare', label: 'Healthcare', dimension: 'human_systems', indicators: ['unmet_medical_needs', 'life_expectancy'] },
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

function formatRegionalValue(value: number, unit?: string) {
  if (unit === 'percent') return `${value.toFixed(1)}%`
  if (unit === 'persons') return new Intl.NumberFormat('en-US', { maximumFractionDigits: 0 }).format(value)
  if (unit === 'people_per_km2') return `${new Intl.NumberFormat('en-US', { maximumFractionDigits: 1 }).format(value)} /km²`
  if (unit === 'eur_per_person') {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'EUR',
      maximumFractionDigits: 0,
    }).format(value)
  }
  if (unit === 'pps_per_person') {
    return `${new Intl.NumberFormat('en-US', { maximumFractionDigits: 0 }).format(value)} PPS/person`
  }
  if (unit === 'usd_ppp_per_person') {
    return `${new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(value)} PPP/person`
  }
  if (unit === 'ug_m3') {
    return `${value.toFixed(1)} µg/m³`
  }
  if (unit === 'celsius') {
    return `${new Intl.NumberFormat('en-US', { maximumFractionDigits: 1 }).format(value)} °C`
  }
  if (unit === 'thousand_passengers') {
    return `${new Intl.NumberFormat('en-US', { maximumFractionDigits: 0 }).format(value)}k passengers`
  }
  if (unit === 'per_100k_people') {
    return `${new Intl.NumberFormat('en-US', { maximumFractionDigits: 1 }).format(value)} /100k`
  }
  if (unit === 'per_1000_people') {
    return `${new Intl.NumberFormat('en-US', { maximumFractionDigits: 1 }).format(value)} /1,000`
  }
  if (unit === 'years') {
    return `${new Intl.NumberFormat('en-US', { maximumFractionDigits: 1 }).format(value)} years`
  }
  if (unit === 'eur_monthly') {
    return `${new Intl.NumberFormat('en-US', { style: 'currency', currency: 'EUR', maximumFractionDigits: 2 }).format(value)} /month`
  }
  if (unit === 'nights_per_person') {
    return `${new Intl.NumberFormat('en-US', { maximumFractionDigits: 1 }).format(value)} nights/resident`
  }
  if (unit === 'm2_per_person') {
    return `${new Intl.NumberFormat('en-US', { maximumFractionDigits: 1 }).format(value)} m²/person`
  }
  if (unit === 'thousand_passengers') {
    return `${new Intl.NumberFormat('en-US', { maximumFractionDigits: 0 }).format(value)}k passengers`
  }
  return new Intl.NumberFormat('en-US', { maximumFractionDigits: 2 }).format(value)
}

function sourceNativeUrbanDomain(indicatorId: string) {
  if (
    indicatorId === 'urban_population'
    || indicatorId === 'urban_population_density'
    || indicatorId.includes('dependency_ratio')
  ) return 'demography'

  if (
    indicatorId.includes('employment_to_population')
    || indicatorId.includes('labour_force')
    || indicatorId.includes('unemployment')
  ) return 'labour'

  if (
    indicatorId.includes('public_transport')
    || indicatorId.includes('commute_')
  ) return 'mobility'

  if (
    indicatorId.includes('green_area')
  ) return 'environment'

  return 'other'
}

function selectedRegionLevelLabel(level: number | string | undefined) {
  if (typeof level === 'number') return `NUTS ${level}`
  if (!level) return 'REGIONAL'
  return level
}

function regionalChangeLabel(points?: Array<{ period: number; value: number }>) {
  if (!points || points.length < 2) return null
  const previous = points[points.length - 2]
  const latest = points[points.length - 1]
  if (previous.value === 0) return null
  const pct = ((latest.value - previous.value) / Math.abs(previous.value)) * 100
  const prefix = pct > 0 ? '+' : ''
  return `${prefix}${pct.toFixed(1)}% vs ${previous.period}`
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

function peerReferenceLabel(peer?: PeerReference) {
  if (!peer || peer.status !== 'available' || peer.rank_low_to_high == null || peer.sample_size < 2) {
    return 'Peer reference unavailable'
  }

  const rank = Number.isInteger(peer.rank_low_to_high)
    ? peer.rank_low_to_high.toFixed(0)
    : peer.rank_low_to_high.toFixed(1)

  return `Peer position ${rank}/${peer.sample_size} · ${peer.adequacy}`
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
  apiBase,
  countries,
  selectedCountry,
  selectedCountryName,
  selectedCountryIso2,
  selectedCountryCenter,
  currentIndicators,
  overviewSeries,
  assessment,
  onCountryChange,
  onOpenIndicators,
  onOpenDimension,
  formatValue,
  dimensionLabels,
}: OverviewPageProps) {
  const [selectedRegion, setSelectedRegion] = useState<{
    id: string
    name: string
    level: number | string
    system: string
  } | null>(null)
  const [selectedCity, setSelectedCity] = useState<{ code: string; name: string } | null>(null)
  const [regionalEvidence, setRegionalEvidence] = useState<RegionalEvidenceResponse | null>(null)
  const [regionalEvidenceState, setRegionalEvidenceState] = useState<'idle' | 'loading' | 'ready' | 'error'>('idle')
  const [cityEvidence, setCityEvidence] = useState<CityEvidenceResponse | null>(null)
  const [cityEvidenceState, setCityEvidenceState] = useState<'idle' | 'loading' | 'ready' | 'error'>('idle')
  const [countryGeographies, setCountryGeographies] = useState<CountryGeography[]>([])
  const [regionSearch, setRegionSearch] = useState('')
  const [urbanSearch, setUrbanSearch] = useState('')
  const [comparisonTarget, setComparisonTarget] = useState('')
  const [geographyComparison, setGeographyComparison] = useState<GeographyComparisonResponse | null>(null)
  const [geographyComparisonState, setGeographyComparisonState] = useState<'idle' | 'loading' | 'ready' | 'error'>('idle')

  useEffect(() => {
    setSelectedRegion(null)
    setSelectedCity(null)
    setRegionalEvidence(null)
    setRegionalEvidenceState('idle')
    setCityEvidence(null)
    setCityEvidenceState('idle')
    setCountryGeographies(geographyCatalogCache.get(selectedCountry) ?? [])
    setRegionSearch('')
    setUrbanSearch('')
    setComparisonTarget('')
    setGeographyComparison(null)
    setGeographyComparisonState('idle')
  }, [selectedCountry])

  useEffect(() => {
    const cached = geographyCatalogCache.get(selectedCountry)
    if (cached) {
      setCountryGeographies(cached)
      return
    }

    const controller = new AbortController()

    fetch(
      `${apiBase}/api/geographies?country_iso3=${encodeURIComponent(selectedCountry)}`,
      { signal: controller.signal },
    )
      .then((response) => {
        if (!response.ok) throw new Error(`Geography catalog HTTP ${response.status}`)
        return response.json() as Promise<GeographyResponse>
      })
      .then((payload) => {
        if (controller.signal.aborted) return
        const geographies = payload.geographies ?? []
        geographyCatalogCache.set(selectedCountry, geographies)
        setCountryGeographies(geographies)
      })
      .catch((error) => {
        if ((error as Error).name === 'AbortError') return
        setCountryGeographies([])
      })

    return () => controller.abort()
  }, [apiBase, selectedCountry])

  useEffect(() => {
    if (!selectedRegion) {
      setRegionalEvidence(null)
      setRegionalEvidenceState('idle')
      return
    }

    const regionalCacheKey = `${selectedRegion.system}:${selectedRegion.id}`
    const cached = regionalEvidenceCache.get(regionalCacheKey)
    if (cached) {
      setRegionalEvidence(cached)
      setRegionalEvidenceState('ready')
      return
    }

    const controller = new AbortController()
    setRegionalEvidenceState('loading')

    const evidencePath = selectedRegion.system === 'NUTS_2024'
      ? `${apiBase}/api/regions/${selectedRegion.id}/evidence?system=NUTS_2024`
      : `${apiBase}/api/geographies/${selectedRegion.id}/evidence?system=${encodeURIComponent(selectedRegion.system)}`

    fetch(
      evidencePath,
      { signal: controller.signal },
    )
      .then((response) => {
        if (!response.ok) throw new Error(`Regional evidence HTTP ${response.status}`)
        return response.json() as Promise<RegionalEvidenceResponse>
      })
      .then((payload) => {
        if (controller.signal.aborted) return
        regionalEvidenceCache.set(regionalCacheKey, payload)
        setRegionalEvidence(payload)
        setRegionalEvidenceState('ready')
      })
      .catch((error) => {
        if ((error as Error).name === 'AbortError') return
        setRegionalEvidence(null)
        setRegionalEvidenceState('error')
      })

    return () => controller.abort()
  }, [apiBase, selectedRegion])

  useEffect(() => {
    setComparisonTarget('')
    setGeographyComparison(null)
    setGeographyComparisonState('idle')
  }, [selectedRegion?.id, selectedRegion?.system])

  useEffect(() => {
    if (!selectedRegion || !comparisonTarget) {
      setGeographyComparison(null)
      setGeographyComparisonState('idle')
      return
    }

    const codes = [selectedRegion.id, comparisonTarget].sort()
    const cacheKey = `${selectedRegion.system}:${codes.join('|')}`
    const cached = geographyComparisonCache.get(cacheKey)
    if (cached) {
      setGeographyComparison(cached)
      setGeographyComparisonState('ready')
      return
    }

    const controller = new AbortController()
    setGeographyComparisonState('loading')
    fetch(
      `${apiBase}/api/geographies/compare?geographies=${codes.map(encodeURIComponent).join(',')}`,
      { signal: controller.signal },
    )
      .then((response) => {
        if (!response.ok) throw new Error(`Geography comparison HTTP ${response.status}`)
        return response.json() as Promise<GeographyComparisonResponse>
      })
      .then((payload) => {
        if (controller.signal.aborted) return
        geographyComparisonCache.set(cacheKey, payload)
        setGeographyComparison(payload)
        setGeographyComparisonState('ready')
      })
      .catch((error) => {
        if ((error as Error).name === 'AbortError') return
        setGeographyComparison(null)
        setGeographyComparisonState('error')
      })

    return () => controller.abort()
  }, [apiBase, selectedRegion, comparisonTarget])

  useEffect(() => {
    if (!selectedCity) {
      setCityEvidence(null)
      setCityEvidenceState('idle')
      return
    }

    const cached = cityEvidenceCache.get(selectedCity.code)
    if (cached) {
      setCityEvidence(cached)
      setCityEvidenceState('ready')
      return
    }

    const controller = new AbortController()
    setCityEvidenceState('loading')

    fetch(`${apiBase}/api/cities/${selectedCity.code}/evidence`, {
      signal: controller.signal,
    })
      .then((response) => {
        if (!response.ok) throw new Error(`City evidence HTTP ${response.status}`)
        return response.json() as Promise<CityEvidenceResponse>
      })
      .then((payload) => {
        if (controller.signal.aborted) return
        cityEvidenceCache.set(selectedCity.code, payload)
        setCityEvidence(payload)
        setCityEvidenceState('ready')
      })
      .catch((error) => {
        if ((error as Error).name === 'AbortError') return
        setCityEvidence(null)
        setCityEvidenceState('error')
      })

    return () => controller.abort()
  }, [apiBase, selectedCity])

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

  const sourceNativeRegions = countryGeographies.filter((item) => (
    !['NUTS_2024', 'URBAN_AUDIT_2024'].includes(item.geography_system)
    && !['city', 'fua'].includes(item.geo_level.toLowerCase())
  ))
  const sourceNativeUrbanAreas = countryGeographies.filter((item) => (
    item.geography_system !== 'URBAN_AUDIT_2024'
    && ['city', 'fua'].includes(item.geo_level.toLowerCase())
  ))

  const regionSearchTerm = regionSearch.trim().toLowerCase()
  const urbanSearchTerm = urbanSearch.trim().toLowerCase()
  const filteredSourceNativeRegions = sourceNativeRegions.filter((item) => {
    if (!regionSearchTerm) return true
    return [
      item.name,
      item.source_geo_code,
      item.geo_level,
    ].some((value) => String(value ?? '').toLowerCase().includes(regionSearchTerm))
  })
  const filteredSourceNativeUrbanAreas = sourceNativeUrbanAreas.filter((item) => {
    if (!urbanSearchTerm) return true
    return [
      item.name,
      item.source_geo_code,
      item.geo_level,
    ].some((value) => String(value ?? '').toLowerCase().includes(urbanSearchTerm))
  })

  const selectedComparisonLevel = selectedRegion
    ? (
        typeof selectedRegion.level === 'number'
          ? `nuts${selectedRegion.level}`
          : String(selectedRegion.level).toLowerCase()
      )
    : null
  const comparisonCandidates = selectedRegion
    ? countryGeographies.filter((item) => (
        item.geography_system === selectedRegion.system
        && item.geo_level.toLowerCase() === selectedComparisonLevel
        && item.source_geo_code !== selectedRegion.id
      ))
    : []

  const geographyCoverage = {
    total: countryGeographies.length,
    regions: countryGeographies.filter((item) => !['city', 'fua'].includes(item.geo_level.toLowerCase())).length,
    cities: countryGeographies.filter((item) => item.geo_level.toLowerCase() === 'city').length,
    fua: countryGeographies.filter((item) => item.geo_level.toLowerCase() === 'fua').length,
    systems: new Set(countryGeographies.map((item) => item.geography_system)).size,
    series: countryGeographies.reduce((sum, item) => sum + (item.indicator_count ?? 0), 0),
  }

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
            {selectedCity ? (
              <span className="countryRegionFocus">CITY · {selectedCity.name} · {selectedCity.code}</span>
            ) : selectedRegion ? (
              <span className="countryRegionFocus">
                {['CITY', 'FUA'].includes(String(selectedRegion.level).toUpperCase()) ? 'URBAN' : 'REGION'}
                {' · '}{selectedRegion.name} · {selectedRegion.id}
              </span>
            ) : null}
            <h3>{selectedCountryName.toUpperCase()}</h3>
            <p>{visual.summary ?? 'Country evidence is active. Regional metrics appear only where verified subnational sources exist.'}</p>
          </div>
        </section>

        <section className="countryRadarMap">
          <div className="radarPanelTopline mapPanelHeader">
            <div>
              <span>MAP</span>
              <strong>Explore country geography and available subnational evidence</strong>
            </div>
            <span className="mapInteractionHint">Scroll to zoom · drag to pan · cities at high zoom</span>
          </div>

          <div
            className={`geographyCoverageStrip ${geographyCoverage.total ? 'available' : 'empty'}`}
            role="region"
            aria-label="Country geographic coverage summary"
          >
            <div>
              <span>Subnational coverage</span>
              <strong>
                {geographyCoverage.total
                  ? `${geographyCoverage.total} geographies · ${geographyCoverage.systems} source system${geographyCoverage.systems === 1 ? '' : 's'}`
                  : 'No integrated subnational evidence'}
              </strong>
            </div>
            <dl>
              <div>
                <dt>Regions</dt>
                <dd>{geographyCoverage.regions}</dd>
              </div>
              <div>
                <dt>Cities</dt>
                <dd>{geographyCoverage.cities}</dd>
              </div>
              <div>
                <dt>FUA</dt>
                <dd>{geographyCoverage.fua}</dd>
              </div>
              <div>
                <dt>Series</dt>
                <dd>{geographyCoverage.series}</dd>
              </div>
            </dl>
          </div>

          {selectedCountryIso2 ? (
            <RegionalMap
              apiBase={apiBase}
              countryIso3={selectedCountry}
              countryIso2={selectedCountryIso2}
              countryCenter={selectedCountryCenter}
              selectedRegion={selectedRegion?.id ?? null}
              selectedCity={selectedCity?.code ?? null}
              selectableCountryIso2={countries.flatMap((country) => country.iso2 ? [country.iso2] : [])}
              onSelectCountry={(iso2) => {
                const country = countries.find((item) => item.iso2 === iso2)
                if (country && country.iso3 !== selectedCountry) {
                  onCountryChange(country.iso3)
                }
              }}
              onSelectRegion={(id, name, level, system) => {
                setSelectedCity(null)
                setSelectedRegion({
                  id,
                  name,
                  level,
                  system: system ?? 'NUTS_2024',
                })
              }}
              onSelectCity={(code, name) => {
                setSelectedRegion(null)
                setSelectedCity({ code, name })
              }}
            />
          ) : (
            <div className="regionalMapState error">Regional map unavailable for this country.</div>
          )}

          {sourceNativeRegions.length ? (
            <div className="sourceNativeGeographyPicker">
              <div>
                <span>AVAILABLE REGIONS</span>
                <strong>Official source-native geography</strong>
                <small>{filteredSourceNativeRegions.length}/{sourceNativeRegions.length} shown</small>
              </div>
              <input
                type="search"
                aria-label="Filter available source-native region"
                value={regionSearch}
                placeholder="Filter by name or code…"
                onChange={(event) => setRegionSearch(event.target.value)}
              />
              <select
                aria-label="Available source-native region"
                value={
                  selectedRegion
                    && sourceNativeRegions.some(
                      (item) => item.source_geo_code === selectedRegion.id,
                    )
                    ? selectedRegion.id
                    : ''
                }
                onChange={(event) => {
                  const geography = sourceNativeRegions.find(
                    (item) => item.source_geo_code === event.target.value,
                  )
                  if (!geography) {
                    setSelectedRegion(null)
                    return
                  }
                  setSelectedCity(null)
                  setSelectedRegion({
                    id: geography.source_geo_code,
                    name: geography.name ?? geography.source_geo_code,
                    level: geography.geo_level.toUpperCase(),
                    system: geography.geography_system,
                  })
                  setRegionSearch('')
                }}
              >
                <option value="">Select a region…</option>
                {filteredSourceNativeRegions.map((item) => (
                  <option key={item.geo_id} value={item.source_geo_code}>
                    {item.name ?? item.source_geo_code} · {item.geo_level.toUpperCase()} · {item.indicator_count} series
                  </option>
                ))}
              </select>
            </div>
          ) : null}

          {sourceNativeUrbanAreas.length ? (
            <div className="sourceNativeGeographyPicker sourceNativeUrbanPicker">
              <div>
                <span>AVAILABLE URBAN AREAS</span>
                <strong>OECD city / Functional Urban Area evidence</strong>
                <small>{filteredSourceNativeUrbanAreas.length}/{sourceNativeUrbanAreas.length} shown</small>
              </div>
              <input
                type="search"
                aria-label="Filter available source-native urban area"
                value={urbanSearch}
                placeholder="Filter by name or code…"
                onChange={(event) => setUrbanSearch(event.target.value)}
              />
              <select
                aria-label="Available source-native urban area"
                value={
                  selectedRegion
                    && sourceNativeUrbanAreas.some(
                      (item) => item.source_geo_code === selectedRegion.id,
                    )
                    ? selectedRegion.id
                    : ''
                }
                onChange={(event) => {
                  const geography = sourceNativeUrbanAreas.find(
                    (item) => item.source_geo_code === event.target.value,
                  )
                  if (!geography) {
                    setSelectedRegion(null)
                    return
                  }
                  setSelectedCity(null)
                  setSelectedRegion({
                    id: geography.source_geo_code,
                    name: geography.name ?? geography.source_geo_code,
                    level: geography.geo_level.toUpperCase(),
                    system: geography.geography_system,
                  })
                  setUrbanSearch('')
                }}
              >
                <option value="">Select an urban area…</option>
                {filteredSourceNativeUrbanAreas.map((item) => (
                  <option key={item.geo_id} value={item.source_geo_code}>
                    {item.name ?? item.source_geo_code} · {item.geo_level.toUpperCase()}
                  </option>
                ))}
              </select>
            </div>
          ) : null}
        </section>

        {(selectedRegion || selectedCity) ? (
          <section className="recentChangesPanel geographicEvidencePanel" aria-label="Selected geographic evidence">
            <div className="radarPanelTopline">
              <div>
                <span>
                  {selectedCity
                    ? 'CITY EVIDENCE'
                    : typeof selectedRegion?.level === 'number'
                      ? `NUTS ${selectedRegion.level} EVIDENCE`
                      : `${selectedRegion?.level ?? 'REGIONAL'} EVIDENCE`}
                </span>
                <strong>{selectedCity?.name ?? selectedRegion?.name}</strong>
              </div>
              <span className="mapInteractionHint">
                {selectedCity?.code ?? selectedRegion?.id}
              </span>
            </div>

            {selectedCity ? (
              <div className="geoEvidenceCompact">
                <div className="geoEvidenceStatus">
                  <span>Urban Audit + EEA</span>
                  <strong>
                    {cityEvidenceState === 'loading'
                      ? 'Loading city evidence…'
                      : cityEvidenceState === 'error'
                        ? 'City evidence unavailable'
                        : cityEvidence
                          ? `${cityEvidence.available_count}/${cityEvidence.indicator_count} series available`
                          : 'City selected'}
                  </strong>
                </div>
                {cityEvidenceState === 'ready' && cityEvidence ? (
                  <div className="cityEvidenceDomainStack">
                    {[
                      ['demography', 'Demography'],
                      ['mobility', 'Mobility'],
                      ['tourism', 'Tourism'],
                      ['environment', 'Environment'],
                    ].map(([category, label]) => {
                      const indicators = cityEvidence.indicators.filter(
                        (indicator) => (indicator.category ?? 'other') === category,
                      )
                      if (!indicators.length) return null

                      return (
                        <section key={category} className="cityEvidenceDomain">
                          <div className="cityEvidenceDomainHeader">
                            <strong>{label}</strong>
                            <span>
                              {indicators.filter((indicator) => indicator.status === 'available').length}
                              /{indicators.length} available
                            </span>
                          </div>
                          <div className="geoEvidenceMetricGrid">
                            {indicators.map((indicator) => (
                              <article key={indicator.indicator_id} className="geoEvidenceMetric">
                                <span>{indicator.name}</span>
                                <strong>
                                  {indicator.status === 'available' && indicator.value != null
                                    ? formatRegionalValue(indicator.value, indicator.unit)
                                    : '—'}
                                </strong>
                                <small>
                                  {indicator.status === 'available'
                                    ? `${indicator.period} · ${indicator.source_id} · ${indicator.dataset_id}`
                                    : 'Official city observation unavailable'}
                                </small>
                              </article>
                            ))}
                          </div>
                        </section>
                      )
                    })}
                  </div>
                ) : null}
                <p className="geoEvidenceScope">
                  Urban Audit cities · population from Eurostat · observed air quality from validated EEA monitoring where available.
                </p>
              </div>
            ) : (
              <div className="geoEvidenceCompact">
                <div className="geoEvidenceStatus">
                  <span>{regionalEvidence?.source ?? 'Regional evidence'}</span>
                  <strong>
                    {regionalEvidenceState === 'loading'
                      ? 'Loading regional evidence…'
                      : regionalEvidenceState === 'error'
                        ? 'Regional evidence unavailable'
                        : regionalEvidence
                          ? regionalEvidence.available_count === 0
                            ? 'No official regional series available for this geographic code'
                            : `${regionalEvidence.available_count}/${regionalEvidence.indicator_count} series available`
                          : 'Region selected'}
                  </strong>
                </div>
                {regionalEvidenceState === 'ready' && regionalEvidence && (
                  ['CITY', 'FUA'].includes(String(selectedRegion?.level).toUpperCase())
                    && selectedRegion?.system === 'OECD_FUA'
                    ? (
                      <div className="cityEvidenceDomainStack">
                        {[
                          ['demography', 'Demography'],
                          ['labour', 'Labour'],
                          ['mobility', 'Mobility'],
                          ['environment', 'Environment'],
                          ['other', 'Other'],
                        ].map(([domain, label]) => {
                          const indicators = regionalEvidence.indicators.filter(
                            (indicator) => sourceNativeUrbanDomain(indicator.indicator_id) === domain,
                          )
                          if (!indicators.length) return null

                          return (
                            <section key={domain} className="cityEvidenceDomain">
                              <div className="cityEvidenceDomainHeader">
                                <strong>{label}</strong>
                                <span>
                                  {indicators.filter((indicator) => indicator.status === 'available').length}
                                  /{indicators.length} available
                                </span>
                              </div>
                              <div className="geoEvidenceMetricGrid">
                                {indicators.map((indicator) => (
                                  <article key={indicator.indicator_id} className="geoEvidenceMetric">
                                    <span>{indicator.name}</span>
                                    <strong>
                                      {indicator.status === 'available' && indicator.value != null
                                        ? formatRegionalValue(indicator.value, indicator.unit)
                                        : '—'}
                                    </strong>
                                    <small>
                                      {indicator.status === 'available'
                                        ? `${indicator.period} · ${indicator.dataset_id}`
                                        : 'Official urban observation unavailable for this code'}
                                    </small>
                                  </article>
                                ))}
                              </div>
                            </section>
                          )
                        })}
                      </div>
                    )
                    : (
                      <div className="geoEvidenceMetricGrid">
                        {regionalEvidence.indicators.map((indicator) => (
                          <article key={indicator.indicator_id} className="geoEvidenceMetric">
                            <span>{indicator.name}</span>
                            <strong>
                              {indicator.status === 'available' && indicator.value != null
                                ? formatRegionalValue(indicator.value, indicator.unit)
                                : '—'}
                            </strong>
                            <small>
                              {indicator.status === 'available'
                                ? `${indicator.period} · ${indicator.dataset_id}`
                                : 'Official regional observation unavailable for this code'}
                            </small>
                          </article>
                        ))}
                      </div>
                    )
                )}
                {regionalEvidenceState === 'ready'
                  && regionalEvidence?.sector_structure?.status === 'available'
                  && regionalEvidence.sector_structure.top_sectors?.length ? (
                  <div className="regionalSectorContext">
                    <strong>Regional employment structure</strong>
                    <span>Employment composition · not vacancy demand</span>
                    <div className="regionalSectorList">
                      {regionalEvidence.sector_structure.top_sectors.slice(0, 5).map((sector) => (
                        <article key={sector.nace_code}>
                          <span>{sector.nace_code} · {sector.nace_label ?? 'Sector'}</span>
                          <strong>
                            {sector.employment_share_pct != null
                              ? `${sector.employment_share_pct.toFixed(1)}%`
                              : `${sector.employment_thousands.toFixed(1)}k`}
                          </strong>
                        </article>
                      ))}
                    </div>
                  </div>
                ) : null}
                {regionalEvidenceState === 'ready'
                  && regionalEvidence?.environmental_health?.status === 'available'
                  && regionalEvidence.environmental_health.metrics?.length ? (
                  <div className="regionalSectorContext">
                    <strong>PM2.5 attributable health burden</strong>
                    <span>EEA health-impact evidence · absolute counts, not a population-normalized regional ranking</span>
                    <div className="regionalSectorList">
                      {regionalEvidence.environmental_health.metrics.map((metric) => (
                        <article key={`${metric.burden_type}-${metric.unit_code}`}>
                          <span>
                            {metric.burden_type === 'PMD'
                              ? 'Premature deaths'
                              : metric.burden_type === 'YLL'
                                ? 'Years of life lost'
                                : metric.label}
                          </span>
                          <strong>{new Intl.NumberFormat('en-US', { maximumFractionDigits: 0 }).format(metric.value)}</strong>
                          <small>
                            {metric.period} · {metric.unit_label}
                            {metric.obs_status ? ` · status ${metric.obs_status}` : ''}
                            {' · do not compare directly across differently sized regions'}
                          </small>
                        </article>
                      ))}
                    </div>
                  </div>
                ) : null}
                {selectedRegion && comparisonCandidates.length ? (
                  <div className="geographyComparePanel" role="region" aria-label="Geography comparison">
                    <div className="geographyCompareHeader">
                      <div>
                        <span>COMPARE LIKE-FOR-LIKE</span>
                        <strong>{selectedRegion.name}</strong>
                      </div>
                      <select
                        aria-label="Compare selected geography with"
                        value={comparisonTarget}
                        onChange={(event) => setComparisonTarget(event.target.value)}
                      >
                        <option value="">Compare with…</option>
                        {comparisonCandidates.map((item) => (
                          <option key={item.geo_id} value={item.source_geo_code}>
                            {item.name ?? item.source_geo_code}
                          </option>
                        ))}
                      </select>
                    </div>
                    {geographyComparisonState === 'loading' ? (
                      <span className="geographyCompareState">Loading comparison…</span>
                    ) : geographyComparisonState === 'error' ? (
                      <span className="geographyCompareState error">Comparison unavailable</span>
                    ) : geographyComparisonState === 'ready' && geographyComparison ? (
                      <div className="geographyCompareRows">
                        {geographyComparison.indicators
                          .filter((item) => (
                            item.regions[selectedRegion.id]?.status === 'available'
                            && item.regions[comparisonTarget]?.status === 'available'
                          ))
                          .slice(0, 8)
                          .map((item) => {
                            const current = item.regions[selectedRegion.id]!
                            const other = item.regions[comparisonTarget]!
                            return (
                              <article key={item.indicator_id}>
                                <span>{item.name}</span>
                                <div>
                                  <strong>{formatRegionalValue(current.value ?? 0, current.unit ?? item.unit ?? undefined)}</strong>
                                  <small>vs</small>
                                  <strong>{formatRegionalValue(other.value ?? 0, other.unit ?? item.unit ?? undefined)}</strong>
                                </div>
                              </article>
                            )
                          })}
                      </div>
                    ) : null}
                    <small className="geographyCompareNote">
                      Same geography system and level only · descriptive comparison · no ranking
                    </small>
                  </div>
                ) : null}
                <p className="geoEvidenceScope">
                  Subnational evidence stays separate from the national Country Radar.
                </p>
              </div>
            )}
          </section>
        ) : (
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

        )}
      </div>

      {selectedRegion ? (
        <section className="countryMetricGrid regionalMetricGrid" aria-label="Regional metric cards">
          {(regionalEvidenceState === 'ready' && regionalEvidence
            ? regionalEvidence.indicators
            : []
          ).map((indicator) => (
            <article
              key={indicator.indicator_id}
              className={`countryMetricCard regionalMetricCard ${indicator.status === 'available' ? 'neutral' : 'unavailable'}`}
            >
              <div className="countryMetricTop">
                <span>{selectedRegion.name}</span>
                <small>{selectedRegionLevelLabel(selectedRegion.level)}</small>
              </div>

              <div className="countryMetricIdentity">
                <span className="countryMetricIcon neutral">•</span>
                <strong className="countryMetricName">{indicator.name}</strong>
              </div>

              <div className="countryMetricEvidenceRow">
                <div>
                  <div className="countryMetricValue">
                    {indicator.status === 'available' && indicator.value != null
                      ? formatRegionalValue(indicator.value, indicator.unit)
                      : '—'}
                  </div>
                  <div className="countryMetricTrend">
                    <strong>{indicator.period ?? '—'}</strong>
                    <span>
                      {indicator.status === 'available'
                        ? regionalChangeLabel(indicator.history) ?? 'latest regional observation'
                        : 'regional evidence unavailable'}
                    </span>
                  </div>
                </div>

                <div className="countryMetricSparkline" aria-label={`${indicator.name} regional history`}>
                  {indicator.history && indicator.history.length >= 2 ? (
                    <svg viewBox="0 0 112 42" role="img">
                      <polyline points={sparklinePoints(indicator.history)} />
                      {indicator.history.map((point, pointIndex, allPoints) => {
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
                  {indicator.status === 'available' ? 'Regional evidence' : 'Coverage gap'}
                </span>
                <span>{indicator.source_id.replaceAll('_', ' ')} · {indicator.dataset_id}</span>
              </div>
            </article>
          ))}

          {regionalEvidenceState === 'loading' && (
            <article className="countryMetricCard regionalMetricCard unavailable">
              <div className="countryMetricTop">
                <span>{selectedRegion.name}</span>
                <small>{selectedRegionLevelLabel(selectedRegion.level)}</small>
              </div>
              <strong className="countryMetricName">Loading regional evidence…</strong>
            </article>
          )}

          {regionalEvidenceState === 'error' && (
            <article className="countryMetricCard regionalMetricCard unavailable">
              <div className="countryMetricTop">
                <span>{selectedRegion.name}</span>
                <small>{selectedRegionLevelLabel(selectedRegion.level)}</small>
              </div>
              <strong className="countryMetricName">Regional evidence unavailable</strong>
            </article>
          )}
        </section>
      ) : (
        <section className="countryMetricGrid" aria-label="Country metric cards">
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
                      {peerReferenceLabel(item.peer_reference)}
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
      )}

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
