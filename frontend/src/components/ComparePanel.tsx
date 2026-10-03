import { useMemo, useState } from 'react'
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

  const descriptiveInsights = useMemo(() => {
    return allIndicators
      .map((item) => {
        const entries = selected
          .map((iso3) => ({ iso3, value: item.countries[iso3] }))
          .filter((entry): entry is { iso3: string; value: ComparisonCountryValue } => Boolean(entry.value))
        if (entries.length < 2) return null
        const max = [...entries].sort((a, b) => b.value.value - a.value.value)[0]
        const min = [...entries].sort((a, b) => a.value.value - b.value.value)[0]
        const spread = Math.abs(max.value.value - min.value.value)
        return {
          indicator: item,
          max,
          min,
          spread,
        }
      })
      .filter(Boolean)
      .sort((a, b) => (b?.spread ?? 0) - (a?.spread ?? 0))
      .slice(0, 3)
  }, [allIndicators, selected])

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
                {visibleIndicators.map((item) => (
                  <tr key={item.indicator_id}>
                    <td>
                      <span className="matrixDomain">{dimensionLabels[item.dimension] ?? item.dimension}</span>
                      <strong>{item.name}</strong>
                    </td>
                    {selected.map((iso3) => {
                      const value = item.countries[iso3]
                      return (
                        <td key={iso3}>
                          {value ? (
                            <>
                              <strong>{formatValue(value.value, item.unit)}</strong>
                              <small>{value.period} · {value.source_id.replaceAll('_', ' ')}</small>
                            </>
                          ) : (
                            <span className="comparisonMissing">No evidence</span>
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

        <aside className="decisionInsightsRail">
          <section>
            <div className="panelHeading">
              <div><span>INSIGHTS</span><h3>Largest measured differences</h3></div>
            </div>
            <div className="decisionInsightList">
              {descriptiveInsights.map((entry) => {
                if (!entry) return null
                const maxCountry = countries.find((country) => country.iso3 === entry.max.iso3)
                const minCountry = countries.find((country) => country.iso3 === entry.min.iso3)
                return (
                  <article key={entry.indicator.indicator_id}>
                    <strong>{entry.indicator.name}</strong>
                    <span>
                      Highest measured value: {maxCountry?.name ?? entry.max.iso3} · {formatValue(entry.max.value.value, entry.indicator.unit)}
                    </span>
                    <small>
                      Lowest measured value: {minCountry?.name ?? entry.min.iso3} · {formatValue(entry.min.value.value, entry.indicator.unit)}
                    </small>
                  </article>
                )
              })}
              {descriptiveInsights.length === 0 && <span>No comparable evidence loaded.</span>}
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
