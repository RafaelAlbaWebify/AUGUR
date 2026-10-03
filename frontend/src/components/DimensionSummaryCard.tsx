type Signal = {
  name: string
  pct_change_5y: number | null
}

type DimensionAssessment = {
  trajectory: string
  confidence: string
  indicator_count: number
  directional_indicator_count: number
  improving_signals: Signal[]
  deteriorating_signals: Signal[]
  stable_signals: Signal[]
  contextual_signals: Signal[]
}

type DimensionSummaryCardProps = {
  label: string
  item: DimensionAssessment
  onOpen?: () => void
}

function tone(trajectory: string) {
  if (trajectory === 'improving') return 'positive'
  if (trajectory === 'deteriorating') return 'negative'
  if (trajectory === 'mixed' || trajectory === 'limited_evidence') return 'warning'
  return 'neutral'
}

function icon(trajectory: string) {
  if (trajectory === 'improving') return '↗'
  if (trajectory === 'deteriorating') return '↘'
  if (trajectory === 'mixed') return '−'
  return '•'
}

export default function DimensionSummaryCard({
  label,
  item,
  onOpen,
}: DimensionSummaryCardProps) {
  const improving = item.improving_signals.map((signal) => signal.name)
  const deteriorating = item.deteriorating_signals.map((signal) => signal.name)

  return (
    <article
      className={`mockDimensionCard ${tone(item.trajectory)} ${onOpen ? 'clickable' : ''}`}
      role={onOpen ? 'button' : undefined}
      tabIndex={onOpen ? 0 : undefined}
      aria-label={onOpen ? `Open ${label} dimension` : undefined}
      onClick={onOpen}
      onKeyDown={onOpen ? (event) => {
        if (event.key === 'Enter' || event.key === ' ') {
          event.preventDefault()
          onOpen()
        }
      } : undefined}
    >
      <div className="mockDimensionHeader">
        <span>{label}</span>
        <small>
          {item.directional_indicator_count > 0
            ? `${item.confidence} trend evidence`
            : 'contextual evidence'}
        </small>
      </div>

      <div className="mockDimensionStatusRow">
        <span className="trajectoryIcon">{icon(item.trajectory)}</span>
        <strong>{item.trajectory.replace('_', ' ')}</strong>
        <small className="signalEvidenceCount">
          {item.directional_indicator_count > 0
            ? `${item.indicator_count} indicators · ${item.directional_indicator_count} directional`
            : `${item.indicator_count} indicators · none directional`}
        </small>
      </div>

      <ul>
        {improving.slice(0, 2).map((signal) => (
          <li className="good" key={signal}>{signal}</li>
        ))}
        {deteriorating.slice(0, 2).map((signal) => (
          <li className="warn" key={signal}>{signal}</li>
        ))}
        {improving.length === 0 && deteriorating.length === 0 && (
          <li className="neutral">Context-dependent signals</li>
        )}
      </ul>
    </article>
  )
}
