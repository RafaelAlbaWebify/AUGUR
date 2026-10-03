import ComparePanel from './ComparePanel'
import DimensionSummaryCard from './DimensionSummaryCard'
import FitSnapshot from './FitSnapshot'
import OverallSignalBalance from './OverallSignalBalance'
import WorldMap from './WorldMap'
import type { DashboardLayout } from './LayoutControls'
import './overview-page.css'

type Country = {
  iso2?: string
  iso3: string
  name: string
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
  layout: DashboardLayout
}

const DIMENSION_ORDER = [
  'prosperity',
  'productive_capacity',
  'housing',
  'demography',
  'human_systems',
  'fiscal',
  'strategic_resilience',
]

export default function OverviewPage({
  apiBase,
  countries,
  selectedCountry,
  selectedCountryName,
  assessment,
  scenarios,
  compareCountries,
  comparison,
  onCountryChange,
  onCompareCountryChange,
  onOpenOutlook,
  onOpenCompare,
  onOpenDimension,
  formatValue,
  dimensionLabels,
  layout,
}: OverviewPageProps) {
  const firstScenario = scenarios?.indicators?.[0] ?? null

  const preview = firstScenario
    ? {
        name: firstScenario.name,
        unit: firstScenario.unit,
        optimistic: firstScenario.scenarios.improvement,
        baseline: firstScenario.scenarios.baseline,
        stress: firstScenario.scenarios.stress,
      }
    : null


  return (
    <section className="overviewPageV2" aria-label="Country overview">
      <div className={`overviewHeroGrid ${layout.topOrder === 'fit-map' ? 'fitFirst' : ''}`}>
        <section className="overviewMapPanel">
          <WorldMap
            countries={countries}
            selectedCountry={selectedCountry}
            onSelectCountry={onCountryChange}
          />
        </section>

        <section className="overviewFitPanel">
          <FitSnapshot apiBase={apiBase} targetCountry={selectedCountry} />
        </section>
      </div>

      <div className="overviewLowerGrid">
        <section className="overviewDimensionsPanel">
          <div className="overviewSectionHeader">
            <div>
              <span>KEY DIMENSIONS</span>
              <h2>{selectedCountryName} at a glance</h2>
            </div>
            <small>trajectory · confidence · contributing signals</small>
          </div>

          <div className="overviewDimensionGridV2">
            {DIMENSION_ORDER.map((dimension) => {
              const item = assessment?.dimensions?.[dimension]
              if (!item) return null

              return (
                <DimensionSummaryCard
                  key={dimension}
                  label={dimensionLabels[dimension] ?? dimension}
                  item={item}
                  onOpen={() => onOpenDimension(dimension)}
                />
              )
            })}
          </div>
        </section>

        <aside className={`overviewInsightRail ${layout.utilityOrder === 'compare-outlook' ? 'compareFirst' : ''}`}>
          <OverallSignalBalance dimensions={assessment?.dimensions} />

          <section className="overviewOutlookCard">
            <div className="overviewRailHeader">
              <div>
                <span>OUTLOOK</span>
                <strong>Official baseline + AUGUR envelope</strong>
              </div>
              <button type="button" onClick={onOpenOutlook}>Open</button>
            </div>

            {preview ? (
              <div className="overviewScenarioPreview">
                <p>{preview.name}</p>
                {[
                  ['Baseline', preview.baseline, 'official'],
                  ['Improvement', preview.optimistic, 'AUGUR model'],
                  ['Stress', preview.stress, 'AUGUR model'],
                ].map(([label, value, provenance]) => {
                  const numericValue = value as number
                  return (
                    <div className="overviewScenarioRow evidenceOnly" key={label as string}>
                      <span>{label}</span>
                      <small>{provenance}</small>
                      <strong>{formatValue(numericValue, preview.unit)}</strong>
                    </div>
                  )
                })}
              </div>
            ) : (
              <div className="overviewRailEmpty">Scenario evidence loading…</div>
            )}
          </section>

          <section className="overviewCompareCard">
            <div className="overviewRailHeader">
              <div>
                <span>COMPARE</span>
                <strong>Country snapshot</strong>
              </div>
              <button type="button" onClick={onOpenCompare}>Open</button>
            </div>

            <ComparePanel
              compact
              countries={countries}
              selected={compareCountries}
              onChange={onCompareCountryChange}
              comparison={comparison}
              formatValue={formatValue}
              dimensionLabels={dimensionLabels}
            />
          </section>
        </aside>
      </div>
    </section>
  )
}
