# AUGUR

Explore where countries are heading — and what those futures mean for you.

AUGUR is a local-first country trajectory and personal-fit analysis platform.

## Phase 0

The first milestone validates the local architecture:

- FastAPI backend
- React + TypeScript + Vite frontend
- SQLite application state
- DuckDB analytical store
- automated tests
- PowerShell start/stop scripts
- frontend/backend health check

## Quick start

### Prerequisites

- Python 3.13+
- Node.js 22+ / npm
- Git

### Setup

```powershell
.\setup-phase0.ps1
```

### Start

```powershell
.\start-augur.ps1
```

Open:

- Frontend: http://127.0.0.1:5173
- Backend: http://127.0.0.1:8000
- API docs: http://127.0.0.1:8000/docs

### Stop

```powershell
.\stop-augur.ps1
```

## Privacy

AUGUR is local-first. Runtime databases, caches, environment files and personal profile data are excluded from version control.
