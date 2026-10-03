import { useMemo, useState } from 'react'

type CurrentIndicator = {
  indicator_id: string
  name: string
  period: number
  value: number
  unit: string
  source_id: string
}

type TrajectoryIndicator = {
  indicator_id: string
  name: string
  period: number
  value: number
  unit: string
  source_id: string
  source_name: string
  dataset_id: string
  source_updated_at?: string | null
}

type TrajectoryResponse = {
  horizons: Array<{
    year: number
    sources: string[]
    indicators: TrajectoryIndicator[]
  }>
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
  horizons: number[]
  indicators: ScenarioIndicator[]
  notes: string[]
}

type FuturePathsPageProps = {
  countryName: string
  currentIndicators: CurrentIndicator[]
  trajectory: TrajectoryResponse | null
  scenarios: ScenarioResponse | null
  formatValue: (value: number, unit: string) => string
}

type ChartBounds = {
  minYear: number
  maxYear: number
  minValue: number
  maxValue: number
}

function boundsFor(series: Array<Array<{ year: number; value: number }>>): ChartBounds | null {
  const values = series.flat()
  if (!values.length) return null
  return {
    minYear: Math.min(...values.map((item) => item.year)),
    maxYear: Math.max(...values.map((item) => item.year)),
    minValue: Math.min(...values.map((item) => item.value)),
    maxValue: Math.max(...values.map((item) => item.value)),
  }
}

function pointsFor(
  values: Array<{ year: number; value: number }>,
  bounds?: ChartBounds | null,
  width = 520,
  height = 230,
) {
  if (!values.length) return ''
  const ownBounds = bounds ?? boundsFor([values])
  if (!ownBounds) return ''
  const { minYear, maxYear, minValue, maxValue } = ownBounds
  const rangeYear = Math.max(1, maxYear - minYear)
  const rangeValue = Math.max(1e-9, maxValue - minValue)

  return values.map((item) => {
    const x = 26 + ((item.year - minYear) / rangeYear) * (width - 52)
    const y = 20 + (1 - ((item.value - minValue) / rangeValue)) * (height - 40)
    return `${x.toFixed(1)},${y.toFixed(1)}`
  }).join(' ')
}

export default function FuturePathsPage({
  countryName,
  currentIndicators,
  trajectory,
  scenarios,
  formatValue,
}: FuturePathsPageProps) {
  const available = useMemo(() => {
    const map = new Map<string, { id: string; name: string; unit: string }>()
    for (const horizon of trajectory?.horizons ?? []) {
      for (const item of horizon.indicators) {
        map.set(item.indicator_id, { id: item.indicator_id, name: item.name, unit: item.unit })
      }
    }
    for (const item of scenarios?.indicators ?? []) {
      map.set(item.indicator_id, { id: item.indicator_id, name: item.name, unit: item.unit })
    }
    return [...map.values()]
  }, [trajectory, scenarios])

  const [selectedId, setSelectedId] = useState<string>('')
  const effectiveId = selectedId || available[0]?.id || ''

  const official = useMemo(() => {
    const rows: TrajectoryIndicator[] = []
    for (const horizon of trajectory?.horizons ?? []) {
      const item = horizon.indicators.find((candidate) => candidate.indicator_id === effectiveId)
      if (item) rows.push(item)
    }
    return rows.sort((a, b) => a.period - b.period)
  }, [trajectory, effectiveId])

  const scenarioRows = useMemo(
    () => (scenarios?.indicators ?? [])
      .filter((item) => item.indicator_id === effectiveId)
      .sort((a, b) => a.period - b.period),
    [scenarios, effectiveId],
  )

  const current = currentIndicators.find((item) => item.indicator_id === effectiveId)
  const selectedMeta = available.find((item) => item.id === effectiveId)
  const unit = selectedMeta?.unit ?? current?.unit ?? ''
  const officialWithCurrent = [
    ...(current ? [{ year: current.period, value: current.value }] : []),
    ...official.map((item) => ({ year: item.period, value: item.value })),
  ]
  const baselinePoints = scenarioRows.map((item) => ({ year: item.period, value: item.scenarios.baseline }))
  const improvementPoints = scenarioRows.map((item) => ({ year: item.period, value: item.scenarios.improvement }))
  const stressPoints = scenarioRows.map((item) => ({ year: item.period, value: item.scenarios.stress }))
  const scenarioBounds = boundsFor([baselinePoints, improvementPoints, stressPoints])

  const sourceNames = [...new Set(official.map((item) => item.source_name))]
  const latestUpdate = official.map((item) => item.source_updated_at).filter(Boolean).at(-1)
  const hasScenarios = scenarioRows.some((item) =>
    Math.abs(item.scenarios.improvement - item.scenarios.baseline) > 1e-9 ||
    Math.abs(item.scenarios.stress - item.scenarios.baseline) > 1e-9
  )

  return (
    <section className="futurePathsPage" aria-label="Outlook">
      <div className="productPageHeader">
        <div>
          <span>3. FUTURE PATHS / Outlook</span>
          <h2>Official forecasts with clearly separated AUGUR scenarios</h2>
        </div>
        <p>{countryName} · official forecast first, model assumptions second.</p>
      </div>

      <section className="futureControlBar">
        <label>
          <span>Indicator</span>
          <select value={effectiveId} onChange={(event) => setSelectedId(event.target.value)}>
            {available.map((item) => <option value={item.id} key={item.id}>{item.name}</option>)}
          </select>
        </label>
        <div className="futureViewToggle">
          <span>View</span>
          <strong>Official forecast + AUGUR scenarios</strong>
        </div>
        <div className="futureViewToggle">
          <span>Forecast horizons</span>
          <strong>{official.map((item) => item.period).join(' · ') || 'No official coverage'}</strong>
        </div>
      </section>

      <div className="futurePathsGrid">
        <section className="forecastPanel">
          <div className="panelHeading">
            <div>
              <span>OFFICIAL FORECAST</span>
              <h3>{selectedMeta?.name ?? 'No official forecast loaded'}</h3>
            </div>
            <small>{sourceNames.join(' · ') || 'No source'}</small>
          </div>

          {officialWithCurrent.length >= 2 ? (
            <div className="forecastChart">
              <svg viewBox="0 0 520 230" role="img" aria-label="Official forecast path">
                <line x1="26" y1="210" x2="494" y2="210" />
                <line x1="26" y1="20" x2="26" y2="210" />
                <polyline className="officialLine" points={pointsFor(officialWithCurrent)} />
                {officialWithCurrent.map((item) => {
                  const pts = pointsFor(officialWithCurrent).split(' ')
                  const [x, y] = pts[officialWithCurrent.indexOf(item)].split(',')
                  return <circle key={item.year} cx={x} cy={y} r="4" className="officialPoint" />
                })}
              </svg>
              <div className="chartLegend">
                {current && <span>Historical/current · {current.period}</span>}
                <span>Official forecast · {official.map((item) => item.period).join(', ')}</span>
              </div>
            </div>
          ) : (
            <div className="evidenceUnavailable">
              <strong>Official forecast series unavailable for this indicator.</strong>
              <span>AUGUR does not interpolate missing official horizons.</span>
            </div>
          )}

          <div className="forecastDetails">
            <div><span>Source</span><strong>{sourceNames.join(' · ') || 'Unavailable'}</strong></div>
            <div><span>Latest source update</span><strong>{latestUpdate ?? 'Unavailable'}</strong></div>
            <div><span>Method</span><strong>Official forecast / projection</strong></div>
          </div>
        </section>

        <section className="scenarioPanel">
          <div className="panelHeading">
            <div>
              <span>AUGUR MODEL SCENARIOS</span>
              <h3>Illustrative alternative paths</h3>
            </div>
            <small>not official forecasts</small>
          </div>

          {scenarioRows.length && hasScenarios ? (
            <div className="forecastChart">
              <svg viewBox="0 0 520 230" role="img" aria-label="AUGUR scenario paths">
                <line x1="26" y1="210" x2="494" y2="210" />
                <line x1="26" y1="20" x2="26" y2="210" />
                <polyline className="scenarioLine improvement" points={pointsFor(improvementPoints, scenarioBounds)} />
                <polyline className="scenarioLine baseline" points={pointsFor(baselinePoints, scenarioBounds)} />
                <polyline className="scenarioLine stress" points={pointsFor(stressPoints, scenarioBounds)} />
              </svg>
              <div className="scenarioLegend">
                <span className="improvement">Improvement</span>
                <span className="baseline">Baseline</span>
                <span className="stress">Stress</span>
              </div>
            </div>
          ) : (
            <div className="evidenceUnavailable">
              <strong>No directional scenario envelope is applied.</strong>
              <span>This indicator is contextual or no model assumptions exist for it.</span>
            </div>
          )}

          <div className="scenarioAssumptionsPanel">
            {scenarioRows.length ? (
              <>
                <div><strong>Baseline</strong><span>Matches the official forecast.</span></div>
                <div><strong>Improvement</strong><span>{hasScenarios ? 'AUGUR assumption; see indicator-specific rule below.' : 'No directional adjustment.'}</span></div>
                <div><strong>Stress</strong><span>{hasScenarios ? 'AUGUR assumption; horizon-scaled model path.' : 'No directional adjustment.'}</span></div>
                <p>{scenarioRows[0]?.assumption}</p>
              </>
            ) : (
              <p>No AUGUR scenario evidence loaded for this indicator.</p>
            )}
          </div>
        </section>
      </div>

      <section className="futureEvidenceFooter">
        <p>
          Official forecast values are displayed as source evidence. AUGUR scenarios are separate model assumptions and must not be read as official probabilities.
        </p>
        <div><span>Evidence</span><strong>{official.length ? 'Official forecast available' : 'Limited'}</strong></div>
        <div><span>Source</span><strong>{sourceNames.join(' · ') || '—'}</strong></div>
        <div><span>Latest value</span><strong>{current ? formatValue(current.value, unit) : '—'}</strong></div>
      </section>
    </section>
  )
}
