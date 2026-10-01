type Country = {
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
  const selectedMeta = selected.map((iso3) =>
    countries.find((country) => country.iso3 === iso3),
  )

  const visibleIndicators = compact
    ? (comparison?.indicators ?? [])
        .filter((item) => PREVIEW_INDICATORS.includes(item.indicator_id))
        .slice(0, 3)
    : comparison?.indicators ?? []

  return (
    <section className={compact ? 'comparePanel compact' : 'comparePanel'}>
      <div className="comparePanelHeader">
        <div>
          <div className="label">COMPARE</div>
          <strong>{compact ? 'Custom comparison' : 'Country comparison'}</strong>
        </div>
        <span>{compact ? 'select countries' : 'aligned indicators · no ranking'}</span>
      </div>

      <div
        className="compareSelectors"
        aria-label={compact ? 'Preview comparison countries' : 'Comparison countries'}
      >
        {selected.map((iso3, index) => (
          <label key={index}>
            <span>{index + 1}</span>
            <select
              aria-label={`${compact ? 'Preview compare' : 'Compare'} country ${index + 1}`}
              value={iso3}
              onChange={(event) => onChange(index, event.target.value)}
            >
              {countries.map((country) => (
                <option key={country.iso3} value={country.iso3}>
                  {country.name}
                </option>
              ))}
            </select>
          </label>
        ))}
      </div>

      {compact ? (
        <div className="comparePreviewRows">
          {visibleIndicators.length === 0 && (
            <div className="comparePreviewEmpty">
              Comparison evidence loading…
            </div>
          )}

          {visibleIndicators.map((item) => (
            <div className="comparePreviewRow" key={item.indicator_id}>
              <span>{item.name}</span>
              <div>
                {selected.map((iso3) => {
                  const value = item.countries[iso3]
                  const country = selectedMeta[selected.indexOf(iso3)]
                  return (
                    <small key={iso3}>
                      <b>{country?.name ?? iso3}</b>
                      {value ? formatValue(value.value, item.unit) : '—'}
                    </small>
                  )
                })}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="comparisonTableWrap">
          <table className="comparisonTable">
            <thead>
              <tr>
                <th>Indicator</th>
                {selected.map((iso3) => (
                  <th key={iso3}>
                    {countries.find((country) => country.iso3 === iso3)?.name ?? iso3}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {visibleIndicators.map((item) => (
                <tr key={item.indicator_id}>
                  <td>
                    <strong>{item.name}</strong>
                    <small>{dimensionLabels[item.dimension] ?? item.dimension}</small>
                  </td>
                  {selected.map((iso3) => {
                    const value = item.countries[iso3]
                    return (
                      <td key={iso3}>
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
      )}
    </section>
  )
}
