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
  improving_signals?: Signal[]
  deteriorating_signals?: Signal[]
  stable_signals?: Signal[]
  contextual_signals?: Signal[]
}

type OverviewSeriesItem = {
  indicator_id: string
  name: string
  dimension: string
  unit: string
  source_id: string
  points: Array<{ period: number; value: number }>
}

type IndicatorsPageProps = {
  countryName: string
  indicators: Indicator[]
  overviewSeries: OverviewSeriesItem[]
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


function sparklinePoints(points: Array<{ period: number; value: number }>) {
  if (points.length < 2) return ''
  const width = 300
  const height = 100
  const pad = 8
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

export default function IndicatorsPage({
  countryName,
  indicators,
  overviewSeries,
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
  const selectedSeries = selected
    ? overviewSeries.find((item) => item.indicator_id === selected.indicator_id)
    : undefined
  const directionalCount = rows.filter((item) =>
    ['improving', 'deteriorating', 'within_target'].includes(item.trend?.interpretation ?? '')
  ).length

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

      {!dimension && (
        <section className="evidenceExplorerSummary" aria-label="Indicator evidence summary">
          <div><span>Indicators shown</span><strong>{rows.length}</strong></div>
          <div><span>Directional signals</span><strong>{directionalCount}</strong></div>
          <div><span>Sources represented</span><strong>{new Set(rows.map((item) => qualityById.get(item.indicator_id)?.preferred_source_name ?? item.source_id)).size}</strong></div>
          <p>Raw percentage changes are descriptive. Directional interpretation is shown separately in the Trend column.</p>
        </section>
      )}

      {dimension && assessment?.[dimension] && (
        <section className="dimensionSynthesis">
          <div className="dimensionSynthesisHeader">
            <div>
              <span>SYNTHESIS</span>
              <h3>{dimensionLabels[dimension] ?? dimension}</h3>
            </div>
            <strong className={`dimensionTrajectoryBadge ${assessment[dimension].trajectory}`}>
              {assessment[dimension].trajectory.replaceAll('_', ' ')}
            </strong>
          </div>

          <div className="dimensionSignalLanes">
            <section className="dimensionSignalLane supporting">
              <div><span>SUPPORTING</span><strong>Improving evidence</strong></div>
              {(assessment[dimension].improving_signals ?? []).length ? (
                (assessment[dimension].improving_signals ?? []).map((signal) => (
                  <article key={signal.indicator_id}>
                    <strong>{signal.name}</strong>
                    <span>{signal.pct_change_5y == null ? '5y change unavailable' : `${changeLabel(signal.pct_change_5y)} over 5y`}</span>
                    <small>{signal.confidence} trend evidence</small>
                  </article>
                ))
              ) : (
                <p>No improving directional signals.</p>
              )}
            </section>

            <section className="dimensionSignalLane opposing">
              <div><span>OPPOSING</span><strong>Deteriorating evidence</strong></div>
              {(assessment[dimension].deteriorating_signals ?? []).length ? (
                (assessment[dimension].deteriorating_signals ?? []).map((signal) => (
                  <article key={signal.indicator_id}>
                    <strong>{signal.name}</strong>
                    <span>{signal.pct_change_5y == null ? '5y change unavailable' : `${changeLabel(signal.pct_change_5y)} over 5y`}</span>
                    <small>{signal.confidence} trend evidence</small>
                  </article>
                ))
              ) : (
                <p>No deteriorating directional signals.</p>
              )}
            </section>

            <section className="dimensionSignalLane contextual">
              <div><span>CONTEXT</span><strong>Stable / contextual evidence</strong></div>
              {[...(assessment[dimension].stable_signals ?? []), ...(assessment[dimension].contextual_signals ?? [])].length ? (
                [...(assessment[dimension].stable_signals ?? []), ...(assessment[dimension].contextual_signals ?? [])].map((signal) => (
                  <article key={signal.indicator_id}>
                    <strong>{signal.name}</strong>
                    <span>{signal.direction.replaceAll('_', ' ')}</span>
                    <small>{signal.confidence} evidence depth</small>
                  </article>
                ))
              ) : (
                <p>No stable/contextual signals.</p>
              )}
            </section>
          </div>
        </section>
      )}

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
                      <td className="rawChange">{changeLabel(item.trend?.pct_change_1y)}</td>
                      <td className="rawChange">{changeLabel(item.trend?.pct_change_3y)}</td>
                      <td className="rawChange">{changeLabel(item.trend?.pct_change_5y)}</td>
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

              <section className="indicatorHistoryPanel" aria-label="Observed indicator history">
                <div className="indicatorHistoryHeader">
                  <span>Observed history</span>
                  <small>{selectedSeries?.points.length ?? 0} points · {selectedSeries?.source_id.replaceAll('_', ' ') ?? 'source unavailable'}</small>
                </div>
                {selectedSeries?.points && selectedSeries.points.length >= 2 ? (
                  <>
                    <svg viewBox="0 0 300 100" role="img" aria-label={`${selected.name} observed history`}>
                      <polyline points={sparklinePoints(selectedSeries.points)} />
                      {selectedSeries.points.map((point, index, allPoints) => {
                        const [cx, cy] = sparklinePoints(allPoints).split(' ')[index].split(',')
                        return <circle key={point.period} cx={cx} cy={cy} r={index === allPoints.length - 1 ? 3.4 : 2} />
                      })}
                    </svg>
                    <div className="indicatorHistoryAxis">
                      <span>{selectedSeries.points[0].period}</span>
                      <span>{selectedSeries.points[selectedSeries.points.length - 1].period}</span>
                    </div>
                  </>
                ) : (
                  <div className="indicatorHistoryEmpty">Observed history unavailable for this indicator.</div>
                )}
              </section>

              <div className="detailChangeGrid">
                <div><span>1 year</span><strong>{changeLabel(selected.trend?.pct_change_1y)}</strong></div>
                <div><span>3 years</span><strong>{changeLabel(selected.trend?.pct_change_3y)}</strong></div>
                <div><span>5 years</span><strong>{changeLabel(selected.trend?.pct_change_5y)}</strong></div>
              </div>

              <dl className="indicatorDetailList">
                <div><dt>Trend</dt><dd>{trendLabel(selected.trend)}</dd></div>
                <div><dt>Trend evidence confidence</dt><dd>{selected.trend?.confidence ?? 'pending'}</dd></div>
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
