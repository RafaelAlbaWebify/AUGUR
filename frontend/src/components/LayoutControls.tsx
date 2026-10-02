export type DashboardLayout = {
  topSplit: number
  bottomSplit: number
  topOrder: 'map-fit' | 'fit-map'
  utilityOrder: 'outlook-compare' | 'compare-outlook'
  showFit: boolean
  showOutlook: boolean
  showCompare: boolean
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
          <span>LAYOUT</span>
          <strong>Dashboard arrangement</strong>
        </div>
        <button type="button" onClick={onClose} aria-label="Close layout settings">×</button>
      </div>

      <label className="layoutSlider">
        <span>Map / Personal Fit</span>
        <input
          type="range"
          min="40"
          max="65"
          value={layout.topSplit}
          onChange={(event) =>
            onChange({ ...layout, topSplit: Number(event.target.value) })
          }
        />
        <small>{layout.topSplit}% / {100 - layout.topSplit}%</small>
      </label>

      <label className="layoutSlider">
        <span>Dimensions / Utility</span>
        <input
          type="range"
          min="65"
          max="82"
          value={layout.bottomSplit}
          onChange={(event) =>
            onChange({ ...layout, bottomSplit: Number(event.target.value) })
          }
        />
        <small>{layout.bottomSplit}% / {100 - layout.bottomSplit}%</small>
      </label>

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
        <span>Utility rail</span>
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

      <div className="layoutChecks">
        <label>
          <input
            type="checkbox"
            checked={layout.showFit}
            onChange={(event) => onChange({ ...layout, showFit: event.target.checked })}
          />
          Personal Fit
        </label>
        <label>
          <input
            type="checkbox"
            checked={layout.showOutlook}
            onChange={(event) => onChange({ ...layout, showOutlook: event.target.checked })}
          />
          Outlook
        </label>
        <label>
          <input
            type="checkbox"
            checked={layout.showCompare}
            onChange={(event) => onChange({ ...layout, showCompare: event.target.checked })}
          />
          Compare
        </label>
      </div>

      <div className="layoutControlsFooter">
        <button type="button" onClick={onReset}>Reset layout</button>
        <small>Saved automatically in this browser.</small>
      </div>
    </section>
  )
}
