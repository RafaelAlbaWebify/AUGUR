import { Fragment, useMemo, useState } from 'react'
import CountrySelect from './CountrySelect'
import FlagIcon from './FlagIcon'

type Country = {
  iso2?: string
  iso3: string
  name: string
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

type ComparePanelProps = {
  countries: Country[]
  selected: string[]
  onChange: (slot: number, iso3: string) => void
  comparison: ComparisonResponse | null
  formatValue: (value: number, unit: string) => string
  dimensionLabels: Record<string, string>
  compact?: boolean
}

const PREVIEW_INDICATORS = [
  'real_gdp_per_capita',
  'unemployment_rate',
  'household_price_level_index',
]


function selectedSetPosition(
  item: ComparisonIndicator,
  iso3: string,
  selected: string[],
) {
  const entries = selected
    .map((country) => ({ iso3: country, value: item.countries[country]?.value }))
    .filter((entry): entry is { iso3: string; value: number } => typeof entry.value === 'number')

  if (entries.length < 2) return null
  const values = entries.map((entry) => entry.value)
  const min = Math.min(...values)
  const max = Math.max(...values)
  const current = entries.find((entry) => entry.iso3 === iso3)
  if (!current) return null
  if (Math.abs(max - min) < 1e-9) return { label: 'Aligned', position: 50 }

  const sorted = [...entries].sort((a, b) => a.value - b.value)
  const rank = sorted.findIndex((entry) => entry.iso3 === iso3)
  const label = rank === 0 ? 'Low' : rank === sorted.length - 1 ? 'High' : 'Mid'
  const position = ((current.value - min) / (max - min)) * 100
  return { label, position }
}

export default function ComparePanel({
  countries,
  selected,
  onChange,
  comparison,
  formatValue,
  dimensionLabels,
  compact = false,
}: ComparePanelProps) {
  const [mode, setMode] = useState<'objective' | 'priorities'>('objective')
  const [dimension, setDimension] = useState('all')
  const selectedMeta = selected.map((iso3) =>
    countries.find((country) => country.iso3 === iso3),
  )

  const allIndicators = comparison?.indicators ?? []
  const visibleIndicators = compact
    ? allIndicators.filter((item) => PREVIEW_INDICATORS.includes(item.indicator_id)).slice(0, 3)
    : allIndicators.filter((item) => dimension === 'all' || item.dimension === dimension)

  const dimensions = useMemo(
    () => [...new Set(allIndicators.map((item) => item.dimension))],
    [allIndicators],
  )

  const groupedIndicators = useMemo(() => {
    const groups = new Map<string, ComparisonIndicator[]>()
    for (const item of visibleIndicators) {
      const bucket = groups.get(item.dimension) ?? []
      bucket.push(item)
      groups.set(item.dimension, bucket)
    }
    return [...groups.entries()].map(([dimensionId, items]) => ({ dimensionId, items }))
  }, [visibleIndicators])

  const countrySummaries = useMemo(() => {
    return selected.map((iso3) => {
      let higher = 0
      let mid = 0
      let lower = 0
      let aligned = 0
      let covered = 0

      for (const item of visibleIndicators) {
        if (!item.countries[iso3]) continue
        covered += 1
        const position = selectedSetPosition(item, iso3, selected)
        if (!position) continue
        if (position.label === 'High') higher += 1
        else if (position.label === 'Low') lower += 1
        else if (position.label === 'Mid') mid += 1
        else aligned += 1
      }

      return { iso3, covered, higher, mid, lower, aligned }
    })
  }, [visibleIndicators, selected])

  const domainCoverage = useMemo(() => {
    return groupedIndicators.map((group) => ({
      dimensionId: group.dimensionId,
      indicatorCount: group.items.length,
      completeCount: group.items.filter((item) =>
        selected.every((iso3) => Boolean(item.countries[iso3]))
      ).length,
    }))
  }, [groupedIndicators, selected])

  const descriptiveInsights = useMemo(() => {
    return visibleIndicators
      .map((item) => {
        const entries = selected
          .map((iso3) => ({ iso3, value: item.countries[iso3] }))
          .filter((entry): entry is { iso3: string; value: ComparisonCountryValue } => Boolean(entry.value))
        if (entries.length < 2) return null
        const max = [...entries].sort((a, b) => b.value.value - a.value.value)[0]
        const min = [...entries].sort((a, b) => a.value.value - b.value.value)[0]
        const spread = Math.abs(max.value.value - min.value.value)
        const denominator = Math.max(Math.abs(max.value.value), Math.abs(min.value.value), 1e-9)
        const relativeSpreadPct = (spread / denominator) * 100
        return {
          indicator: item,
          max,
          min,
          spread,
          relativeSpreadPct,
        }
      })
      .filter(Boolean)
      .sort((a, b) => (b?.relativeSpreadPct ?? 0) - (a?.relativeSpreadPct ?? 0))
      .slice(0, 3)
  }, [visibleIndicators, selected])

  if (compact) {
    return (
      <section className="comparePanel compact">
        <div className="comparePanelHeader">
          <div>
            <div className="label">COMPARE</div>
            <strong>Country snapshot</strong>
          </div>
          <span>objective evidence</span>
        </div>

        <div className="compareSelectors" aria-label="Preview comparison countries">
          {selected.map((iso3, index) => (
            <div className="compareSelectorSlot" key={index}>
              <span>{index + 1}</span>
              <CountrySelect
                countries={countries}
                value={iso3}
                onChange={(next) => onChange(index, next)}
                ariaLabel={`Preview compare country ${index + 1}`}
                compact
              />
            </div>
          ))}
        </div>

        <div className="compareBarPreview">
          {visibleIndicators.slice(0, 1).map((item) => {
            const numericValues = selected
              .map((iso3) => item.countries[iso3]?.value)
              .filter((value): value is number => typeof value === 'number')
            const maxValue = numericValues.length ? Math.max(...numericValues) : 0

            return (
              <div key={item.indicator_id}>
                <div className="compareMetricLabel">
                  <span>{item.name}</span>
                  <small>relative within selected set</small>
                </div>
                <div className="compareBarRows">
                  {selected.map((iso3, index) => {
                    const value = item.countries[iso3]
                    const country = selectedMeta[index]
                    const width = value && maxValue > 0 ? Math.max(8, (value.value / maxValue) * 100) : 0
                    return (
                      <div className="compareBarRow" key={iso3}>
                        <span><FlagIcon iso3={iso3} />{country?.name ?? iso3}</span>
                        <div className="compareBarTrack"><i style={{ width: `${width}%` }} /></div>
                        <strong>{value ? formatValue(value.value, item.unit) : '—'}</strong>
                      </div>
                    )
                  })}
                </div>
              </div>
            )
          })}
        </div>
      </section>
    )
  }

  return (
    <section className="decisionMatrixPage" aria-label="Country comparison">
      <div className="productPageHeader">
        <div>
          <span>4. DECISION MATRIX / Compare</span>
          <h2>Compare countries across domains and identify trade-offs</h2>
        </div>
        <p>Objective evidence first. Personal weighting will only activate when a transparent weighting model is implemented.</p>
      </div>

      <section className="decisionControls">
        <div className="segmentedTabs decisionModeTabs">
          <button type="button" className={mode === 'objective' ? 'active' : ''} onClick={() => setMode('objective')}>Objective data</button>
          <button type="button" className={mode === 'priorities' ? 'active' : ''} onClick={() => setMode('priorities')}>My priorities</button>
        </div>

        <label>
          <span>Domains</span>
          <select value={dimension} onChange={(event) => setDimension(event.target.value)}>
            <option value="all">All domains</option>
            {dimensions.map((value) => <option value={value} key={value}>{dimensionLabels[value] ?? value}</option>)}
          </select>
        </label>

        <div className="compareCountrySelectors">
          {selected.map((iso3, index) => (
            <CountrySelect
              key={index}
              countries={countries}
              value={iso3}
              onChange={(next) => onChange(index, next)}
              ariaLabel={`Compare country ${index + 1}`}
              compact
            />
          ))}
        </div>
      </section>

      <section className="decisionSummaryStrip" aria-label="Comparison summary">
        {countrySummaries.map((summary) => {
          const country = countries.find((item) => item.iso3 === summary.iso3)
          return (
            <article key={summary.iso3}>
              <div className="decisionSummaryCountry">
                <FlagIcon iso3={summary.iso3} />
                <div>
                  <strong>{country?.name ?? summary.iso3}</strong>
                  <span>{summary.covered}/{visibleIndicators.length || 0} comparable indicators</span>
                </div>
              </div>
              <div className="decisionSummaryPositions">
                <span><b>{summary.higher}</b> higher values</span>
                <span><b>{summary.mid}</b> mid</span>
                <span><b>{summary.lower}</b> lower values</span>
                {summary.aligned > 0 && <span><b>{summary.aligned}</b> aligned</span>}
              </div>
            </article>
          )
        })}
        <p>
          Higher/lower describes numerical position only. It is not automatically better/worse; interpretation depends on the indicator.
        </p>
      </section>

      <section className="decisionDomainCoverage" aria-label="Domain evidence coverage">
        <div className="panelHeading">
          <div><span>EVIDENCE COVERAGE</span><h3>Comparable data by domain</h3></div>
        </div>
        <div className="decisionCoverageGrid">
          {domainCoverage.map((item) => {
            const pct = item.indicatorCount
              ? (item.completeCount / item.indicatorCount) * 100
              : 0
            return (
              <article key={item.dimensionId}>
                <div>
                  <strong>{dimensionLabels[item.dimensionId] ?? item.dimensionId}</strong>
                  <span>{item.completeCount}/{item.indicatorCount} fully comparable</span>
                </div>
                <div className="decisionCoverageTrack">
                  <i style={{ width: `${pct}%` }} />
                </div>
              </article>
            )
          })}
        </div>
      </section>

      {mode === 'priorities' && (
        <div className="comparisonNotice">
          Personal weighting is not yet implemented. The matrix below remains objective; AUGUR will not simulate a personalized ranking until weights, normalization and sensitivity analysis are explicit.
        </div>
      )}

      <div className="decisionMatrixLayout">
        <section className="decisionTablePanel">
          <div className="decisionTableWrap">
            <table className="decisionMatrixTable">
              <thead>
                <tr>
                  <th>Domain / Indicator</th>
                  {selected.map((iso3) => (
                    <th key={iso3}>
                      <span className="countryHeader"><FlagIcon iso3={iso3} />{countries.find((country) => country.iso3 === iso3)?.name ?? iso3}</span>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {groupedIndicators.map((group) => (
                  <Fragment key={group.dimensionId}>
                    <tr className="matrixDomainRow">
                      <td colSpan={selected.length + 1}>
                        {dimensionLabels[group.dimensionId] ?? group.dimensionId}
                      </td>
                    </tr>
                    {group.items.map((item) => (
                      <tr key={item.indicator_id}>
                        <td>
                          <strong>{item.name}</strong>
                          <small className="matrixIndicatorNote">descriptive comparison · no winner implied</small>
                        </td>
                        {selected.map((iso3) => {
                          const value = item.countries[iso3]
                          const position = selectedSetPosition(item, iso3, selected)
                          return (
                            <td key={iso3}>
                              {value ? (
                                <div className="matrixValueCell">
                                  <div className="matrixValueTop">
                                    <strong>{formatValue(value.value, item.unit)}</strong>
                                    {position && <span className="matrixPositionBadge">{position.label}</span>}
                                  </div>
                                  {position && (
                                    <div className="matrixPositionTrack" aria-label={`${position.label} within selected set`}>
                                      <i style={{ width: `${Math.max(4, position.position)}%` }} />
                                    </div>
                                  )}
                                  <small>{value.period} · {value.source_id.replaceAll('_', ' ')}</small>
                                </div>
                              ) : (
                                <span className="comparisonMissing">No evidence</span>
                              )}
                            </td>
                          )
                        })}
                      </tr>
                    ))}
                  </Fragment>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        <aside className="decisionInsightsRail">
          <section>
            <div className="panelHeading">
              <div><span>INSIGHTS</span><h3>Largest relative spreads</h3></div>
            </div>
            <div className="decisionInsightList">
              {descriptiveInsights.map((entry) => {
                if (!entry) return null
                const maxCountry = countries.find((country) => country.iso3 === entry.max.iso3)
                const minCountry = countries.find((country) => country.iso3 === entry.min.iso3)
                return (
                  <article key={entry.indicator.indicator_id}>
                    <div className="relativeSpreadHeading">
                      <strong>{entry.indicator.name}</strong>
                      <span>{entry.relativeSpreadPct.toFixed(1)}% relative spread</span>
                    </div>
                    <span>
                      High value: {maxCountry?.name ?? entry.max.iso3} · {formatValue(entry.max.value.value, entry.indicator.unit)}
                    </span>
                    <small>
                      Low value: {minCountry?.name ?? entry.min.iso3} · {formatValue(entry.min.value.value, entry.indicator.unit)}
                    </small>
                  </article>
                )
              })}
              {descriptiveInsights.length === 0 && <span>No comparable evidence loaded.</span>}
              {descriptiveInsights.length > 0 && (
                <p className="relativeSpreadNote">
                  Relative spread normalizes each indicator by the largest absolute value in the selected set. It is descriptive, not a quality score.
                </p>
              )}
            </div>
          </section>

          <section>
            <div className="panelHeading">
              <div><span>ROBUSTNESS CHECK</span><h3>How sensitive is the comparison?</h3></div>
            </div>
            <div className="robustnessUnavailable">
              <strong>Not available yet</strong>
              <p>
                A robustness result requires user-defined weights, comparable normalization, missing-data rules and sensitivity analysis. AUGUR will not invent a stability claim before those are implemented.
              </p>
            </div>
          </section>
        </aside>
      </div>
    </section>
  )
}
