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

const DIMENSION_ORDER = [
  'prosperity',
  'productive_capacity',
  'housing',
  'demography',
  'human_systems',
  'fiscal',
  'strategic_resilience',
]

function trendSymbol(direction?: string) {
  if (!direction || direction === 'unknown') return '·'
  if (direction === 'stable') return '→'
  if (direction === 'increase' || direction === 'strong_increase') return '↗'
  return '↘'
}

function trendLabel(trend?: Trend) {
  if (!trend) return 'Trend pending'
  if (trend.interpretation === 'improving') return 'Improving'
  if (trend.interpretation === 'deteriorating') return 'Deteriorating'
  if (trend.interpretation === 'within_target') return 'Within target'
  if (trend.direction === 'stable') return 'Stable'
  return 'Contextual'
}

function trendEvidenceLabel(trend?: Trend) {
  if (!trend) return 'evidence pending'

  const interpreted = ['improving', 'deteriorating', 'within_target'].includes(trend.interpretation)
    || trend.direction === 'stable'

  return interpreted ? `${trend.confidence} trend evidence` : 'contextual evidence'
}

function changeLabel(value: number | null | undefined) {
  if (value == null) return '—'
  const sign = value > 0 ? '+' : ''
  return `${sign}${value.toFixed(1)}%`
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
  const qualityById = new Map(sourceQuality.map((item) => [item.indicator_id, item]))
  const groups = new Map<string, Indicator[]>()

  for (const item of indicators) {
    if (dimension && item.dimension !== dimension) continue
    const group = groups.get(item.dimension) ?? []
    group.push(item)
    groups.set(item.dimension, group)
  }

  const dimensions = dimension
    ? [dimension]
    : DIMENSION_ORDER.filter((item) => groups.has(item))

  return (
    <section className="indicatorEvidencePage" aria-label={dimension ? 'Dimension detail' : 'Indicators'}>
      <div className="dimensionHeader indicatorEvidenceHero">
        <div>
          <div className="label">{dimension ? 'DIMENSION DETAIL' : 'INDICATORS'}</div>
          <h3>
            {dimension
              ? `${dimensionLabels[dimension] ?? dimension} · ${countryName}`
              : `${countryName} evidence`}
          </h3>
        </div>
        <div className="indicatorEvidenceHeroMeta">
          {dimension && onBackToIndicators && (
            <button type="button" onClick={onBackToIndicators}>All indicators</button>
          )}
          <span>{indicators.filter((item) => !dimension || item.dimension === dimension).length} indicators</span>
        </div>
      </div>

      {dimension && assessment?.[dimension] && (
        <section className="dimensionDetailSummary" aria-label="Dimension assessment">
          <div>
            <span>Trajectory</span>
            <strong>{assessment[dimension].trajectory.replaceAll('_', ' ')}</strong>
          </div>
          <div>
            <span>
              {assessment[dimension].directional_indicator_count > 0
                ? 'Trend evidence'
                : 'Evidence type'}
            </span>
            <strong>
              {assessment[dimension].directional_indicator_count > 0
                ? assessment[dimension].confidence
                : 'contextual'}
            </strong>
          </div>
          <div>
            <span>Directional coverage</span>
            <strong>{Math.round(assessment[dimension].coverage * 100)}%</strong>
          </div>
          <p>
            {assessment[dimension].evidence_note
              ?? 'Dimension synthesis is derived from the contributing indicator evidence shown below.'}
          </p>
        </section>
      )}

      {dimensions.map((dimensionId) => {
        const items = groups.get(dimensionId) ?? []
        if (!items.length) return null

        return (
          <section className="dimensionSection indicatorEvidenceDimension" key={dimensionId}>
            <div className="dimensionHeader">
              <div>
                <div className="label">DIMENSION</div>
                <h3>{dimensionLabels[dimensionId] ?? dimensionId}</h3>
              </div>
              {!dimension && onOpenDimension ? (
                <button type="button" className="detailsToggle" onClick={() => onOpenDimension(dimensionId)}>
                  Open dimension
                </button>
              ) : (
                <span>{items.length} indicators</span>
              )}
            </div>

            <div className="indicatorGrid">
              {items.map((indicator) => {
                const quality = qualityById.get(indicator.indicator_id)

                return (
                  <article className="metricCard" key={indicator.indicator_id}>
                    <div className="metricTop">
                      <span className="metricName">{indicator.name}</span>
                      <span className="metricYear">{indicator.period}</span>
                    </div>

                    <div className="metricValue">
                      {formatValue(indicator.value, indicator.unit)}
                    </div>

                    <div className="trendBlock">
                      <div className={`trendState ${indicator.trend?.interpretation ?? ''}`}>
                        <span className="trendArrow">{trendSymbol(indicator.trend?.direction)}</span>
                        <span>{trendLabel(indicator.trend)}</span>
                        <small>{trendEvidenceLabel(indicator.trend)}</small>
                      </div>

                      {indicator.interpretation_policy === 'target_range' && (
                        <div className="targetRule">
                          <span>{indicator.trend?.target_status?.replaceAll('_', ' ') ?? 'target pending'}</span>
                          <span>target {indicator.target_min}–{indicator.target_max}</span>
                        </div>
                      )}

                      <div className="trendChanges">
                        <span>1Y <strong>{changeLabel(indicator.trend?.pct_change_1y)}</strong></span>
                        <span>3Y <strong>{changeLabel(indicator.trend?.pct_change_3y)}</strong></span>
                        <span>5Y <strong>{changeLabel(indicator.trend?.pct_change_5y)}</strong></span>
                      </div>
                    </div>

                    <div className="sourceQuality">
                      <div>
                        <strong>{quality?.preferred_source_name ?? indicator.source_id.replaceAll('_', ' ')}</strong>
                        <span>preferred source · {quality?.preferred_period ?? indicator.period}</span>
                      </div>
                      <div>
                        <strong>
                          {quality?.source_count && quality.source_count > 1
                            ? `${quality.source_count} sources`
                            : 'Single source'}
                        </strong>
                        <span>
                          {quality?.disagreement_pct == null
                            ? 'no same-period comparison'
                            : `${quality.disagreement_pct.toFixed(2)}% disagreement · ${quality.common_period}`}
                        </span>
                      </div>
                    </div>

                    <div className="metricFooter">
                      <span>{indicator.source_id.replaceAll('_', ' ')}</span>
                      <span>{indicator.indicator_id}</span>
                    </div>
                  </article>
                )
              })}
            </div>
          </section>
        )
      })}

      {dimensions.length === 0 && (
        <div className="trajectoryEmpty">No indicator evidence is available for this view.</div>
      )}
    </section>
  )
}
