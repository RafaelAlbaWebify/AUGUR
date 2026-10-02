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

function signalBars(item: DimensionAssessment) {
  const source = [
    ...item.improving_signals,
    ...item.deteriorating_signals,
    ...item.stable_signals,
  ].slice(0, 6)

  if (source.length === 0) {
    return [26, 38, 30, 44, 34, 40]
  }

  return source.map((signal, index) => {
    const magnitude = Math.abs(signal.pct_change_5y ?? 0)
    return Math.min(90, Math.max(24, 28 + magnitude * 3 + index * 3))
  })
}

export default function DimensionSummaryCard({
  label,
  item,
  onOpen,
}: DimensionSummaryCardProps) {
  const improving = item.improving_signals.map((signal) => signal.name)
  const deteriorating = item.deteriorating_signals.map((signal) => signal.name)
  const bars = signalBars(item)

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
        <small>{item.confidence} confidence</small>
      </div>

      <div className="mockDimensionStatusRow">
        <span className="trajectoryIcon">{icon(item.trajectory)}</span>
        <strong>{item.trajectory.replace('_', ' ')}</strong>
        <div className="signalBars" aria-hidden="true">
          {bars.map((height, index) => (
            <i key={index} style={{ height: `${height}%` }} />
          ))}
        </div>
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
