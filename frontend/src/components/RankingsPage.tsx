import { useEffect, useState } from 'react'

type Indicator = 'regional_employment_rate' | 'regional_unemployment_rate'
type RankRow = {
  rank: number; geo_id: string; country_iso3: string
  name: string | null; value: number; unit: string
  period: number; source_id: string; dataset_id: string
}
type RankResponse = {
  status: string; indicator_id: string; period: number; observed_rows: number
  eligible_total: number; excluded_reasons: Record<string, number>
  provider_metadata_issues: Record<string, number>
  items: RankRow[]; has_more: boolean; limit: number; offset: number
}

const indicators: { id: Indicator; name: string }[] = [
  { id: 'regional_employment_rate', name: 'Employment rate (20–64)' },
  { id: 'regional_unemployment_rate', name: 'Unemployment rate (20–64)' },
]
const countries = ['ESP', 'PRT', 'IRL'] as const

export default function RankingsPage({ apiBase }: { apiBase: string }) {
  const params = new URLSearchParams(window.location.search)
  const initialIndicator = params.get('indicator') === 'regional_unemployment_rate'
    ? 'regional_unemployment_rate' : 'regional_employment_rate'
  const [indicator, setIndicator] = useState<Indicator>(initialIndicator)
  const [selected, setSelected] = useState<string[]>(() => {
    const requested = (params.get('countries') ?? 'ESP,PRT,IRL').split(',')
    const valid = countries.filter(code => requested.includes(code))
    return valid.length ? valid : [...countries]
  })
  const [order, setOrder] = useState<'asc' | 'desc'>(params.get('order') === 'desc' ? 'desc' : 'asc')
  const [report, setReport] = useState<RankResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const query = new URLSearchParams({
      indicator, countries: selected.join(','), order,
    })
    window.history.replaceState({}, '', `/rankings?${query}`)
    const controller = new AbortController()
    setLoading(true)
    setError(null)
    const endpoint = `${apiBase}/api/rankings/regions?indicator_id=${indicator}&countries=${selected.join(',')}&order=${order}&limit=50`
    fetch(endpoint, { signal: controller.signal })
      .then(async response => {
        if (!response.ok) throw new Error(`Ranking API HTTP ${response.status}`)
        return response.json() as Promise<RankResponse>
      })
      .then(data => setReport(data))
      .catch(reason => {
        if (!controller.signal.aborted) {
          setReport(null)
          setError(String(reason))
        }
      })
      .finally(() => { if (!controller.signal.aborted) setLoading(false) })
    return () => controller.abort()
  }, [apiBase, indicator, selected, order])

  function toggleCountry(country: string) {
    setSelected(current => current.includes(country)
      ? (current.length > 1 ? current.filter(value => value !== country) : current)
      : [...current, country].sort())
  }

  return (
    <section className="rankingsPage" aria-label="Regional rankings" style={{ maxWidth: 1050, margin: '0 auto', padding: '24px 28px' }}>
      <h2>Regional rankings</h2>
      <p>Eurostat · NUTS2 regions · 2025. Results are shown only when statistical and boundary evidence is certified.</p>
      <div style={{ display: 'flex', gap: 18, flexWrap: 'wrap', alignItems: 'end', marginBottom: 22 }}>
        <label>Indicator
          <select value={indicator} onChange={event => setIndicator(event.target.value as Indicator)}>
            {indicators.map(item => <option key={item.id} value={item.id}>{item.name}</option>)}
          </select>
        </label>
        <fieldset style={{ display: 'flex', gap: 12, border: 0, padding: 0, margin: 0 }}>
          <legend>Countries</legend>
          {countries.map(code => (
            <label key={code}><input type="checkbox" checked={selected.includes(code)}
              onChange={() => toggleCountry(code)} /> {code}</label>
          ))}
        </fieldset>
        <label>Order
          <select value={order} onChange={event => setOrder(event.target.value as 'asc' | 'desc')}>
            <option value="asc">Lowest first</option>
            <option value="desc">Highest first</option>
          </select>
        </label>
      </div>
      {loading && <p role="status">Checking ranking evidence…</p>}
      {error && <p role="alert">Ranking service unavailable: {error}</p>}
      {!loading && report && <>
        <p role="status">
          {report.eligible_total} eligible of {report.observed_rows} stored observations in this scope.
          {report.eligible_total === 0 ? ' No numerical ranking can be shown until the evidence gates pass.' : ''}
        </p>
        {report.status !== 'ready' && <p role="alert"><strong>Ranking blocked:</strong> {report.status.replaceAll('_', ' ')}.
          Stored observations are not proof of statistical or geographic comparability.</p>}
        {Object.keys(report.excluded_reasons).length > 0 && <details>
          <summary>Eligibility exclusions</summary>
          <ul>{Object.entries(report.excluded_reasons).map(([reason, count]) =>
            <li key={reason}>{reason.replaceAll('_', ' ')}: {count}</li>)}</ul>
        </details>}
        {Object.keys(report.provider_metadata_issues).length > 0 && <details>
          <summary>Provider metadata issues</summary>
          <ul>{Object.entries(report.provider_metadata_issues).map(([reason, count]) =>
            <li key={reason}>{reason.replaceAll('_', ' ')}: {count}</li>)}</ul>
        </details>}
        {report.items.length > 0 && <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', marginTop: 18 }}>
            <thead><tr><th scope="col">Rank</th><th scope="col">Region</th><th scope="col">Country</th>
              <th scope="col">Value</th><th scope="col">Year</th><th scope="col">Source</th></tr></thead>
            <tbody>{report.items.map(row => <tr key={row.geo_id}>
              <td>{row.rank}</td><td>{row.name ?? row.geo_id}</td><td>{row.country_iso3}</td>
              <td>{row.value.toFixed(1)} {row.unit}</td><td>{row.period}</td>
              <td><a href={`https://ec.europa.eu/eurostat/databrowser/view/${encodeURIComponent(row.dataset_id)}/default/table?lang=en`}
                target="_blank" rel="noreferrer">{row.source_id}</a></td>
            </tr>)}</tbody>
          </table>
          {report.has_more && <p>More eligible regions are available through the ranking API.</p>}
        </div>}
      </>}
    </section>
  )
}
