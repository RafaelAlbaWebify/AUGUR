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
  const counts = {
    improving: values.filter((item) => item.trajectory === 'improving').length,
    deteriorating: values.filter((item) => item.trajectory === 'deteriorating').length,
    mixed: values.filter((item) => item.trajectory === 'mixed').length,
    stable: values.filter((item) => item.trajectory === 'stable').length,
    contextual: values.filter((item) => item.trajectory === 'contextual').length,
    limited: values.filter((item) => item.trajectory === 'limited_evidence').length,
  }

  const summary = [
    ['improving', counts.improving],
    ['deteriorating', counts.deteriorating],
    ['mixed', counts.mixed],
    ['stable', counts.stable],
    ['contextual', counts.contextual],
    ['limited evidence', counts.limited],
  ]
    .filter(([, count]) => Number(count) > 0)
    .map(([label, count]) => `${count} ${label}`)
    .join(' · ')

  return (
    <section className="overallSignalBalance">
      <div>
        <span>DIMENSION TRAJECTORIES</span>
        <strong>{values.length ? `${values.length} assessed` : 'Loading…'}</strong>
      </div>
      <p>{summary || 'No trajectory evidence available yet.'}</p>
    </section>
  )
}
