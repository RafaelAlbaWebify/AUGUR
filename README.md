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

### Import TTV calibration cases

AUGUR includes a local-only calibration store for anonymous observed TTV cases. This infrastructure does **not** activate the TTV model or mark it externally calibrated.

CSV columns:

```text
case_id,country_iso3,employment_mode,engine_version,composition,candidate_weeks_min,candidate_weeks_max,observed_weeks,sample_role,start_event_definition_version,viability_outcome_definition_version,source_label,observed_at,stage_timings_json
```

Required import columns remain everything through `observed_weeks`. `sample_role` defaults to `development`. Start/outcome definition versions, `source_label`, `observed_at` and `stage_timings_json` are optional for development cases. Holdout imports are blocked while the calibration protocol has no approved version.

When stage-level observations are available, `stage_timings_json` may contain anonymised timings for `legal`, `language`, `skills`, `employment` and `financial`. Each included stage must provide its candidate minimum, candidate maximum and observed weeks.

Example import:

```powershell
.\import-ttv-calibration.ps1 -Path ".\my-calibration-cases.csv"
```

The local SQLite calibration table stores no full personal profile payload. It records only anonymous case identifiers, country, employment mode, candidate range, observed duration and provenance labels.

`check-operability.ps1` reports descriptive calibration metrics:

- observed case count;
- country count;
- candidate-interval coverage;
- mean absolute midpoint error;
- mean signed midpoint error.

These metrics remain descriptive until AUGUR has an approved external-calibration protocol and acceptance criteria.

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

### Build EURES market-evidence review

Annual EURES unit-group updates are prepared as review artifacts rather than written directly into production evidence.

Prerequisites:

- import the full official ESCO dataset;
- normalize the source table to CSV with these columns:

```text
occupation_label,shortage_countries,surplus_countries
```

Country lists use two-letter EURES country codes separated by spaces, commas, semicolons or pipes. An optional `expected_isco` column pins a previously reviewed ISCO-08 unit-group mapping; if the live ESCO resolver returns a different code, the row is rejected for review.

The currently reviewed ICT subset is versioned at:

`backend/app/evidence/eures_shortages_surpluses_2025_ict_normalized.csv`

CI checks that this reviewed table and the production manifest remain identical for those 13 unit groups.

For the current 2025 EURES annex:

```powershell
.\build-eures-market-evidence.ps1 -Path ".\eures-2025-normalized.csv"
```

The command:

1. resolves each occupation label against the local full ESCO dataset;
2. requires a configurable confidence threshold and ambiguity margin;
3. derives the ISCO unit group only from the accepted ESCO match;
4. validates country codes;
5. reports duplicate ISCO assignments;
6. writes `exports\eures_market_review.json`;
7. keeps ambiguous/unresolved rows explicit;
8. **never modifies** `backend/app/evidence/eures_lmi_2025.json` automatically.

Exit code `0` means every row resolved and the artifact is ready for human review. Exit code `2` means unresolved rows remain and production evidence is unchanged.

This workflow is intentionally separate from live synchronization because the official ELA annual material is published as a report/annex and interactive dashboard rather than a stable machine-readable CSV feed.

Official source pages:

- https://www.ela.europa.eu/en/publications/labour-shortages-and-surpluses-europe-2025
- https://www.ela.europa.eu/en/dashboard-ela-quantification-labour-shortages-and-surpluses-europe-2025

## Testing and CI

GitHub Actions runs:

1. backend dependency install and pytest;
2. frontend dependency audit and production build;
3. Chromium Playwright smoke and responsive QA.

The browser suite covers routing, country switching, comparison neutrality, Profile separation, guarded Edit Layout persistence, Overview composition and responsive behaviour across desktop, tablet and mobile viewport sizes.

## Privacy

AUGUR is local-first. Runtime databases, caches, environment files and personal profile data are excluded from version control.


### TTV calibration development data

AUGUR includes an empty development-case template at:

`docs/TTV_CALIBRATION_TEMPLATE.csv`

Observed development cases can be imported locally with:

```powershell
.\import-ttv-calibration.ps1 -Path ".\path\to\observed-development-cases.csv"
```

The calibration store is local and excluded from git. Importing cases does not activate the TTV external-calibration gate. Holdout cases are rejected while the calibration protocol remains unapproved.
