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
- country routing with refresh-safe URLs, including indicator and dimension drill-down
- observed-data snapshots and historical trend analysis
- dimension synthesis
- official outlook and AUGUR scenario envelopes
- neutral multi-country comparison
- local personal profile
- LegalFit, LanguageFit, CareerFit and FinancialFit
- TTV dependency readiness
- local ESCO dataset import and occupation/skill matching pipeline
- responsive Overview, Indicators, Dimension Detail, Profile, Compare and Outlook views
- guarded persistent Edit Layout preferences
- explicit analytical operability status (`ready` / `partial` / `empty`)

AUGUR keeps country evidence separate from personal-fit analysis. Personal profile data can change whether a country fits a household, but never changes country facts, source observations, official forecasts or country trends.

AUGUR deliberately does not report full readiness while TTV duration modelling is unavailable. Country analysis and core Personal Fit evidence can be operational independently through the separate `analysis_ready` state.

Career market evidence coverage is reported separately. Broad EURES evidence exists for the supported countries, while verified ISCO unit-group coverage is intentionally partial and is never described as exhaustive.

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

### Recommended full bootstrap

```powershell
.\bootstrap-augur.ps1
```

This installs the application, runs tests/build, synchronizes the official country-evidence providers and finishes with an operability check.

Without a full ESCO package, country analysis can be operational but CareerFit/TTV evidence remains partial.

To load the official ESCO v1.2.1 English CSV classification, download and extract it from the official ESCO portal and run:

```powershell
.\bootstrap-augur.ps1 -SkipSetup -SkipSync -EscoPath "C:\path\to\esco"
```

### Dependency-only setup

```powershell
.\setup-phase0.ps1
```

The setup script keeps its historical filename. It installs dependencies and validates the codebase, but does **not** synchronize analytical evidence.

### Verify operability

```powershell
.\check-operability.ps1
```

The check reports:

- `ready` — country analysis, full Personal Fit evidence and a validated TTV temporal model are available;
- `partial` — the application can run, but one or more evidence/model layers are incomplete;
- `empty` — analytical evidence has not been loaded.

The check also reports `analysis_ready` separately. This can be true while full AUGUR readiness is still false when the TTV temporal model has not yet been validated.

### Refresh evidence

Use the incremental refresh workflow to keep synchronized evidence inside AUGUR's operability freshness window without rerunning dependency installation:

```powershell
.\refresh-augur.ps1
```

This runs the current multi-provider country evidence synchronization and then `check-operability.ps1`.

The existing ESCO dataset is preserved by default. To import or refresh a full official ESCO package at the same time:

```powershell
.\refresh-augur.ps1 -EscoPath "C:\path\to\esco"
```

Use `-SkipSync` only when you intentionally want to refresh ESCO and re-check operability without synchronizing country evidence.

### Start

```powershell
.\start-augur.ps1
```

Startup reports both runtime health and analytical operability.

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
