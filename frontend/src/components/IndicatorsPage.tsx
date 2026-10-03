import { useMemo, useState } from 'react'

type Trend = {
  direction: string
  interpretation: string
  confidence: string
  pct_change_1y: number | null
  pct_change_3y: number | null
  pct_change_5y: number | null
  target_status: string | null
}

type Indicator = {
  indicator_id: string
  name: string
  dimension: string
  period: number
  value: number
  unit: string
  source_id: string
  source_updated_at?: string | null
  retrieved_at?: string
  trend?: Trend
  interpretation_policy?: string
  target_min?: number | null
  target_max?: number | null
}

type SourceQualityItem = {
  indicator_id: string
  preferred_source_id: string
  preferred_source_name: string
  preferred_period: number
  source_count: number
  common_period: number | null
  disagreement_pct: number | null
}

type DimensionAssessment = {
  trajectory: string
  confidence: string
  indicator_count: number
  directional_indicator_count: number
  coverage: number
  evidence_status?: string
  evidence_note?: string | null
}

type IndicatorsPageProps = {
  countryName: string
  indicators: Indicator[]
  sourceQuality: SourceQualityItem[]
  assessment?: Record<string, DimensionAssessment>
  dimension?: string | null
  dimensionLabels: Record<string, string>
  formatValue: (value: number, unit: string) => string
  onOpenDimension?: (dimension: string) => void
  onBackToIndicators?: () => void
}

function changeLabel(value: number | null | undefined) {
  if (value == null) return '—'
  const sign = value > 0 ? '+' : ''
  return `${sign}${value.toFixed(1)}%`
}

function trendLabel(trend?: Trend) {
  if (!trend) return 'Pending'
  if (trend.interpretation === 'improving') return 'Improving'
  if (trend.interpretation === 'deteriorating') return 'Deteriorating'
  if (trend.interpretation === 'within_target') return 'Within target'
  if (trend.direction === 'stable') return 'Stable'
  return 'Contextual'
}

function qualityLabel(item: SourceQualityItem | undefined, trend?: Trend) {
  if (!item) return trend?.confidence === 'high' ? 'Medium' : 'Limited'
  if (item.source_count >= 2 && (item.disagreement_pct == null || item.disagreement_pct <= 2)) return 'High'
  if (item.source_count >= 2) return 'Medium'
  return trend?.confidence === 'high' ? 'Medium' : 'Limited'
}

function qualityTone(label: string) {
  return label === 'High' ? 'good' : label === 'Medium' ? 'warn' : 'neutral'
}

export default function IndicatorsPage({
  countryName,
  indicators,
  sourceQuality,
  assessment,
  dimension,
  dimensionLabels,
  formatValue,
  onOpenDimension,
  onBackToIndicators,
}: IndicatorsPageProps) {
  const [query, setQuery] = useState('')
  const [domain, setDomain] = useState(dimension ?? 'all')
  const [source, setSource] = useState('all')
  const [quality, setQuality] = useState('all')
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [detailsTab, setDetailsTab] = useState<'details' | 'provenance'>('details')

  const qualityById = useMemo(
    () => new Map(sourceQuality.map((item) => [item.indicator_id, item])),
    [sourceQuality],
  )

  const dimensions = useMemo(
    () => [...new Set(indicators.map((item) => item.dimension))],
    [indicators],
  )
  const sources = useMemo(
    () => [...new Set(indicators.map((item) => qualityById.get(item.indicator_id)?.preferred_source_name ?? item.source_id))],
    [indicators, qualityById],
  )

  const rows = useMemo(() => indicators.filter((item) => {
    if (dimension && item.dimension !== dimension) return false
    if (domain !== 'all' && item.dimension !== domain) return false
    const sourceName = qualityById.get(item.indicator_id)?.preferred_source_name ?? item.source_id
    if (source !== 'all' && sourceName !== source) return false
    const q = qualityLabel(qualityById.get(item.indicator_id), item.trend)
    if (quality !== 'all' && q !== quality) return false
    if (query && !`${item.name} ${item.indicator_id}`.toLowerCase().includes(query.toLowerCase())) return false
    return true
  }), [indicators, dimension, domain, source, quality, query, qualityById])

  const selected = rows.find((item) => item.indicator_id === selectedId)
    ?? rows[0]
    ?? indicators[0]
  const selectedQuality = selected ? qualityById.get(selected.indicator_id) : undefined
  const selectedQualityLabel = selected ? qualityLabel(selectedQuality, selected.trend) : 'Limited'

  return (
    <section className="evidenceExplorerPage" aria-label={dimension ? 'Dimension detail' : 'Indicators'}>
      <div className="productPageHeader evidenceExplorerHeader">
        <div>
          <span>{dimension ? '2. EVIDENCE EXPLORER / Dimension' : '2. EVIDENCE EXPLORER / Indicators'}</span>
          <h2>
            {dimension
              ? `${dimensionLabels[dimension] ?? dimension} · ${countryName}`
              : `Explore the data, sources and trends for ${countryName}`}
          </h2>
        </div>
        {dimension && onBackToIndicators && (
          <button className="secondaryAction" type="button" onClick={onBackToIndicators}>All indicators</button>
        )}
      </div>

      {dimension && assessment?.[dimension] && (
        <section className="dimensionEvidenceStrip">
          <div><span>Trajectory</span><strong>{assessment[dimension].trajectory.replaceAll('_', ' ')}</strong></div>
          <div><span>Directional coverage</span><strong>{Math.round(assessment[dimension].coverage * 100)}%</strong></div>
          <div><span>Evidence state</span><strong>{assessment[dimension].evidence_status?.replaceAll('_', ' ') ?? 'available'}</strong></div>
          <p>{assessment[dimension].evidence_note ?? 'The dimension synthesis is derived from the indicator evidence below.'}</p>
        </section>
      )}

      <div className="evidenceExplorerLayout">
        <section className="evidenceTablePanel">
          <div className="evidenceFilters">
            <input
              aria-label="Search indicators"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Search indicators…"
            />
            <select aria-label="Domain filter" value={domain} onChange={(event) => setDomain(event.target.value)}>
              <option value="all">All domains</option>
              {dimensions.map((value) => <option value={value} key={value}>{dimensionLabels[value] ?? value}</option>)}
            </select>
            <select aria-label="Source filter" value={source} onChange={(event) => setSource(event.target.value)}>
              <option value="all">All sources</option>
              {sources.map((value) => <option value={value} key={value}>{value}</option>)}
            </select>
            <select aria-label="Quality filter" value={quality} onChange={(event) => setQuality(event.target.value)}>
              <option value="all">All quality</option>
              <option value="High">High</option>
              <option value="Medium">Medium</option>
              <option value="Limited">Limited</option>
            </select>
          </div>

          <div className="evidenceTableWrap">
            <table className="evidenceExplorerTable">
              <thead>
                <tr>
                  <th>Indicator</th>
                  <th>Domain</th>
                  <th>Latest value</th>
                  <th>1y</th>
                  <th>3y</th>
                  <th>5y</th>
                  <th>Trend</th>
                  <th>Source</th>
                  <th>Update</th>
                  <th>Quality</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((item) => {
                  const q = qualityById.get(item.indicator_id)
                  const qLabel = qualityLabel(q, item.trend)
                  return (
                    <tr
                      key={item.indicator_id}
                      className={selected?.indicator_id === item.indicator_id ? 'selected' : ''}
                      onClick={() => setSelectedId(item.indicator_id)}
                    >
                      <td>
                        <button
                          type="button"
                          className="indicatorRowButton"
                          onClick={(event) => {
                            event.stopPropagation()
                            if (onOpenDimension && !dimension) onOpenDimension(item.dimension)
                            else setSelectedId(item.indicator_id)
                          }}
                        >
                          {item.name}
                        </button>
                      </td>
                      <td>{dimensionLabels[item.dimension] ?? item.dimension}</td>
                      <td><strong>{formatValue(item.value, item.unit)}</strong><small>{item.period}</small></td>
                      <td className={(item.trend?.pct_change_1y ?? 0) >= 0 ? 'positiveRaw' : 'negativeRaw'}>{changeLabel(item.trend?.pct_change_1y)}</td>
                      <td className={(item.trend?.pct_change_3y ?? 0) >= 0 ? 'positiveRaw' : 'negativeRaw'}>{changeLabel(item.trend?.pct_change_3y)}</td>
                      <td className={(item.trend?.pct_change_5y ?? 0) >= 0 ? 'positiveRaw' : 'negativeRaw'}>{changeLabel(item.trend?.pct_change_5y)}</td>
                      <td><span className={`trendPill ${item.trend?.interpretation ?? 'context'}`}>{trendLabel(item.trend)}</span></td>
                      <td>{q?.preferred_source_name ?? item.source_id.replaceAll('_', ' ')}</td>
                      <td>{q?.preferred_period ?? item.period}</td>
                      <td><span className={`evidenceChip ${qualityTone(qLabel)}`}>{qLabel}</span></td>
                    </tr>
                  )
                })}
                {rows.length === 0 && (
                  <tr><td colSpan={10}>No indicators match the current filters.</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </section>

        <aside className="indicatorDetailsPanel">
          <div className="detailsTabs">
            <button type="button" className={detailsTab === 'details' ? 'active' : ''} onClick={() => setDetailsTab('details')}>Indicator details</button>
            <button type="button" className={detailsTab === 'provenance' ? 'active' : ''} onClick={() => setDetailsTab('provenance')}>Provenance</button>
          </div>

          {selected ? detailsTab === 'details' ? (
            <div className="indicatorDetailsBody">
              <span className="detailDomain">{dimensionLabels[selected.dimension] ?? selected.dimension}</span>
              <h3>{selected.name}</h3>
              <div className="detailValue">{formatValue(selected.value, selected.unit)}</div>
              <small>{selected.period}</small>

              <div className="detailChangeGrid">
                <div><span>1 year</span><strong>{changeLabel(selected.trend?.pct_change_1y)}</strong></div>
                <div><span>3 years</span><strong>{changeLabel(selected.trend?.pct_change_3y)}</strong></div>
                <div><span>5 years</span><strong>{changeLabel(selected.trend?.pct_change_5y)}</strong></div>
              </div>

              <dl className="indicatorDetailList">
                <div><dt>Trend</dt><dd>{trendLabel(selected.trend)}</dd></div>
                <div><dt>Evidence depth</dt><dd>{selected.trend?.confidence ?? 'pending'}</dd></div>
                <div><dt>Policy</dt><dd>{selected.interpretation_policy?.replaceAll('_', ' ') ?? 'contextual'}</dd></div>
                <div><dt>Evidence quality</dt><dd><span className={`evidenceChip ${qualityTone(selectedQualityLabel)}`}>{selectedQualityLabel}</span></dd></div>
              </dl>
            </div>
          ) : (
            <div className="indicatorDetailsBody provenanceBody">
              <h3>{selected.name}</h3>
              <dl className="indicatorDetailList">
                <div><dt>Preferred source</dt><dd>{selectedQuality?.preferred_source_name ?? selected.source_id.replaceAll('_', ' ')}</dd></div>
                <div><dt>Preferred period</dt><dd>{selectedQuality?.preferred_period ?? selected.period}</dd></div>
                <div><dt>Sources available</dt><dd>{selectedQuality?.source_count ?? 1}</dd></div>
                <div><dt>Common period</dt><dd>{selectedQuality?.common_period ?? 'No comparison'}</dd></div>
                <div><dt>Disagreement</dt><dd>{selectedQuality?.disagreement_pct == null ? 'Not measurable' : `${selectedQuality.disagreement_pct.toFixed(2)}%`}</dd></div>
                <div><dt>Indicator ID</dt><dd>{selected.indicator_id}</dd></div>
              </dl>
              <p>Quality is descriptive evidence metadata. AUGUR does not treat source count alone as corroboration.</p>
            </div>
          ) : (
            <div className="indicatorDetailsBody">Select an indicator to inspect its evidence.</div>
          )}
        </aside>
      </div>
    </section>
  )
}
