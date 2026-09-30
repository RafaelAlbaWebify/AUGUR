import { useEffect, useState } from 'react'

type Health = {
  status: string
  phase: number
  version: string
  datastores: {
    sqlite: boolean
    duckdb: boolean
  }
}

export default function App() {
  const [health, setHealth] = useState<Health | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetch('http://127.0.0.1:8000/api/health')
      .then(async (response) => {
        if (!response.ok) throw new Error(`HTTP ${response.status}`)
        return response.json()
      })
      .then(setHealth)
      .catch((err) => setError(String(err)))
  }, [])

  return (
    <main className="shell">
      <header>
        <div>
          <div className="eyebrow">COUNTRY TRAJECTORY & PERSONAL FIT</div>
          <h1>AUGUR</h1>
          <p className="subtitle">
            Interpret present signals. Explore possible futures.
          </p>
        </div>
        <div className={`status ${health?.status === 'ok' ? 'ok' : ''}`}>
          <span className="dot" />
          {health ? `Phase ${health.phase} · ${health.status}` : 'Connecting'}
        </div>
      </header>

      <section className="hero">
        <div>
          <div className="label">LOCAL FOUNDATION</div>
          <h2>Phase 0</h2>
          <p>
            AUGUR is running locally. The first milestone verifies the application
            shell, backend API, frontend, analytical store and local state database.
          </p>
        </div>
      </section>

      <section className="grid">
        <Card title="Backend" value={health ? 'ONLINE' : error ? 'ERROR' : 'CHECKING'} />
        <Card title="SQLite" value={health?.datastores.sqlite ? 'READY' : '—'} />
        <Card title="DuckDB" value={health?.datastores.duckdb ? 'READY' : '—'} />
        <Card title="Next" value="SPAIN DATA" />
      </section>

      {error && (
        <section className="error">
          Backend connection failed: {error}
        </section>
      )}

      <footer>AUGUR v0.1 · Phase 0 foundation</footer>
    </main>
  )
}

function Card({ title, value }: { title: string; value: string }) {
  return (
    <article className="card">
      <div className="label">{title}</div>
      <div className="value">{value}</div>
    </article>
  )
}
