type DimensionAssessment = {
  trajectory: string
}

type OverallSignalBalanceProps = {
  dimensions: Record<string, DimensionAssessment> | undefined
}

export default function OverallSignalBalance({
  dimensions,
}: OverallSignalBalanceProps) {
  const values = Object.values(dimensions ?? {})
  const counts = [
    ['Improving', values.filter((item) => item.trajectory === 'improving').length],
    ['Deteriorating', values.filter((item) => item.trajectory === 'deteriorating').length],
    ['Mixed', values.filter((item) => item.trajectory === 'mixed').length],
    ['Stable', values.filter((item) => item.trajectory === 'stable').length],
    ['Contextual', values.filter((item) => item.trajectory === 'contextual').length],
    ['Limited evidence', values.filter((item) => item.trajectory === 'limited_evidence').length],
  ] as const

  return (
    <section className="overallSignalBalance">
      <div className="trajectorySummaryHeader">
        <span>DIMENSION TRAJECTORIES</span>
        <strong>{values.length ? `${values.length} assessed` : 'Loading…'}</strong>
      </div>

      <div className="trajectoryCountRow" aria-label="Dimension trajectory counts">
        {counts
          .filter(([, count]) => count > 0)
          .map(([label, count]) => (
            <span className="trajectoryCountChip" key={label}>
              <strong>{count}</strong>
              <small>{label}</small>
            </span>
          ))}
      </div>
    </section>
  )
}
