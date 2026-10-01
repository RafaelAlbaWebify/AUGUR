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
  const improving = values.filter((item) => item.trajectory === 'improving').length
  const mixed = values.filter((item) => item.trajectory === 'mixed').length
  const contextual = values.filter((item) =>
    ['contextual', 'limited_evidence', 'stable'].includes(item.trajectory),
  ).length
  const deteriorating = values.filter((item) => item.trajectory === 'deteriorating').length

  let label = 'Balanced'
  let tone = 'neutral'

  if (improving > deteriorating + mixed) {
    label = 'Improving tilt'
    tone = 'positive'
  } else if (deteriorating > improving) {
    label = 'Pressure tilt'
    tone = 'negative'
  } else if (mixed > 0) {
    label = 'Mixed'
    tone = 'warning'
  }

  return (
    <section className="overallSignalBalance">
      <div>
        <span>OVERALL SIGNAL BALANCE</span>
        <strong className={tone}>{label}</strong>
      </div>
      <p>
        {improving} improving · {mixed} mixed · {contextual} contextual
        {deteriorating ? ` · ${deteriorating} deteriorating` : ''}
      </p>
    </section>
  )
}
