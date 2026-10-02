export type DashboardLayout = {
  topOrder: 'map-fit' | 'fit-map'
  utilityOrder: 'outlook-compare' | 'compare-outlook'
}

type LayoutControlsProps = {
  open: boolean
  layout: DashboardLayout
  onChange: (next: DashboardLayout) => void
  onClose: () => void
  onReset: () => void
}

export default function LayoutControls({
  open,
  layout,
  onChange,
  onClose,
  onReset,
}: LayoutControlsProps) {
  if (!open) return null

  return (
    <section className="layoutControls" aria-label="Dashboard layout settings">
      <div className="layoutControlsHeader">
        <div>
          <span>EDIT LAYOUT</span>
          <strong>Safe dashboard arrangement</strong>
        </div>
        <button type="button" onClick={onClose} aria-label="Close layout settings">×</button>
      </div>

      <p className="layoutGuardrailNote">
        Core panels, approved proportions and responsive behaviour stay fixed.
      </p>

      <div className="layoutOptionRow">
        <span>Top row</span>
        <button
          type="button"
          className={layout.topOrder === 'map-fit' ? 'active' : ''}
          onClick={() => onChange({ ...layout, topOrder: 'map-fit' })}
        >
          Map · Fit
        </button>
        <button
          type="button"
          className={layout.topOrder === 'fit-map' ? 'active' : ''}
          onClick={() => onChange({ ...layout, topOrder: 'fit-map' })}
        >
          Fit · Map
        </button>
      </div>

      <div className="layoutOptionRow">
        <span>Insight rail</span>
        <button
          type="button"
          className={layout.utilityOrder === 'outlook-compare' ? 'active' : ''}
          onClick={() => onChange({ ...layout, utilityOrder: 'outlook-compare' })}
        >
          Outlook first
        </button>
        <button
          type="button"
          className={layout.utilityOrder === 'compare-outlook' ? 'active' : ''}
          onClick={() => onChange({ ...layout, utilityOrder: 'compare-outlook' })}
        >
          Compare first
        </button>
      </div>

      <div className="layoutControlsFooter">
        <button type="button" onClick={onReset}>Reset layout</button>
        <small>Saved automatically in this browser.</small>
      </div>
    </section>
  )
}
