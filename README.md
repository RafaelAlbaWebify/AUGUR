# AUGUR

Explore where countries are heading — and what those futures mean for you.

AUGUR is a local-first country trajectory and personal-fit analysis platform.

## Current state

AUGUR has moved beyond its initial architecture-validation milestone.

Implemented capabilities include:

- FastAPI backend
- React + TypeScript + Vite frontend
- SQLite application/profile state
- DuckDB analytical store
- automated backend and browser tests
- PowerShell start/stop scripts
- country routing with refresh-safe URLs
- observed-data snapshots and historical trend analysis
- dimension synthesis
- official outlook and AUGUR scenario envelopes
- neutral multi-country comparison
- local personal profile
- LegalFit, LanguageFit, CareerFit and FinancialFit
- TTV dependency readiness
- local ESCO dataset import and occupation/skill matching pipeline
- responsive Overview, Profile, Compare and Outlook views
- guarded persistent Edit Layout preferences

AUGUR keeps country evidence separate from personal-fit analysis. Personal profile data can change whether a country fits a household, but never changes country facts, source observations, official forecasts or country trends.

## Local ports

AUGUR uses dedicated local ports to avoid conflicts with JOLT and VERIDRA:

- Frontend: http://127.0.0.1:5190
- Backend: http://127.0.0.1:8020
- API docs: http://127.0.0.1:8020/docs

## Quick start

### Prerequisites

- Python 3.13+
- Node.js 22+ / npm
- Git

### Setup

```powershell
.\setup-phase0.ps1
```

The setup script keeps its historical filename, but initializes the current application stack.

### Start

```powershell
.\start-augur.ps1
```

### Stop

```powershell
.\stop-augur.ps1
```

## ESCO

AUGUR seeds a deliberately partial ESCO dataset for pipeline validation.

A full official ESCO CSV package can be imported locally with the repository import tooling. CareerFit only treats ESCO skill evidence as complete when the loaded dataset is in `full` mode.

Occupation resolution is transparent: candidate ESCO occupations include a match score and method, and low-confidence matches are refused rather than silently accepted.

## Testing and CI

GitHub Actions runs:

1. backend dependency install and pytest;
2. frontend dependency audit and production build;
3. Chromium Playwright smoke and responsive QA.

The browser suite covers routing, country switching, comparison neutrality, Profile separation, guarded Edit Layout persistence, Overview composition and responsive behaviour across desktop, tablet and mobile viewport sizes.

## Privacy

AUGUR is local-first. Runtime databases, caches, environment files and personal profile data are excluded from version control.
