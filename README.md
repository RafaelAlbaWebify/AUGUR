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

This runs the current multi-provider country sync, registered-country subnational sync, automatic repair of required local evidence and then `check-operability.ps1`.

OECD provider-native regional and urban refreshes are freshness-aware. By default, countries with OECD evidence retrieved within the last 24 hours are skipped instead of redownloading the same large SDMX datasets. Coverage gaps remain explicit and are not treated as fresh evidence.

To force OECD TL2/TL3 and FUA/city evidence to be downloaded again regardless of local freshness:

```powershell
.\refresh-augur.ps1 -ForceOecdRefresh
```

The existing ESCO dataset is preserved by default. To import or refresh a full official ESCO package at the same time:

```powershell
.\refresh-augur.ps1 -EscoPath "C:\path\to\esco"
```

Use `-SkipSync` only when you intentionally want zero external evidence synchronization. Automatic local-evidence repair is also skipped in this mode.

### TTV external calibration lifecycle

AUGUR's bounded TTV v1 calibration protocol is frozen as `ttv-calibration-protocol-v1`.
The protocol can collect a real holdout, but the temporal model remains unpublished
until that holdout passes the pre-declared criteria and a representativeness review.

The holdout workflow is deliberately explicit:

1. Import a prospective holdout whose rows declare the frozen protocol and event/outcome definitions:

```powershell
.\import-ttv-holdout.ps1 -Path ".\path\to\ttv-holdout.csv"
```

2. After the full holdout has been collected, seal it. Sealing requires at least 60
   cases, records a canonical SHA-256 fingerprint and prevents additional holdout
   cases from being added under this protocol:

```powershell
.\seal-ttv-holdout.ps1
```

3. Record the separate representativeness/cohort-coverage review:

```powershell
.\review-ttv-holdout.ps1 `
  -Representative yes `
  -CohortCoverageAdequate yes `
  -ReviewerLabel "methodology-review-v1"
```

4. Inspect the complete gate state:

```powershell
.\check-operability.ps1
```

Even when every calibration gate passes, AUGUR does **not** assign
`TEMPORAL_MODEL_VERSION` automatically. Publishing a temporal model remains an
explicit versioned release decision. Synthetic, retrospectively tuned or
post-hoc promoted development cases must not be used as the final holdout.

### Global country baseline

ESP / PRT / IRL remain AUGUR's validation set for regression and operability gating, but they are no longer the product boundary.

AUGUR can discover the World Bank country catalog, register real countries dynamically, and ingest a broad national baseline from global official sources in batches.

Run the global baseline explicitly with:

```powershell
.\sync-global-baseline.ps1
```

or as part of the normal refresh workflow:

```powershell
.\refresh-augur.ps1 -GlobalBaseline
```

The global baseline currently uses:

- World Bank WDI for broad observed national indicators;
- UN World Population Prospects for demographic history and official projections;
- IMF DataMapper where the source is reachable from the current environment.

A country is **registered** when authoritative metadata identify it. A country is **analyzable** only after AUGUR has stored real analytical observations for it. Discovered countries with no evidence are not surfaced in the normal country selector.

Coverage can be inspected through:

- `GET /api/countries/coverage` for national registration and analyzability;
- `GET /api/geographies/coverage` for provider-neutral regional/city coverage.
- `GET /api/geographies/coverage/indicators` for **observed** per-indicator reach among registered geographies. Optional query parameters: `country_iso3`, `geography_system`, and `geo_level`.

The indicator-coverage endpoint reports distinct geographies with an actual stored observation, registered-geography denominators, per-geography latest-observation period ranges, **same-period coverage by observed year**, and ingestion timestamp ranges (under the explicit `earliest_ingestion_by_geography` and `most_recent_ingestion` fields). It does not invent absent indicator rows when no verified expected-indicator catalog is available. Coverage ratios are descriptive and are **not** provider-universe completeness percentages, data quality scores or evidence freshness guarantees. Dataset ingestion timestamps must never be presented as the year of the underlying source observation.

For example, with AUGUR running locally:

```powershell
Invoke-RestMethod 'http://127.0.0.1:8020/api/geographies/coverage/indicators?country_iso3=ESP&geography_system=OECD_TL_2024&geo_level=tl2' | ConvertTo-Json -Depth 8
```

The response is based only on the local DuckDB store; it does not trigger a provider fetch, and an empty result does not prove the OECD has no data.


NUTS 2024 and Urban Audit remain European geography providers, not AUGUR's universal geography model. Non-European regional/city providers register their own native geography system and level through the provider-neutral geography registry.

GitHub-hosted runners currently receive HTTP 403 from both IMF DataMapper v2 and v1. Live smoke tests report this explicitly as a CI transport restriction rather than treating it as missing country evidence; normal local ingestion still attempts IMF.

### TTV calibration development workflow

AUGUR includes a local-first TTV calibration workflow. This infrastructure does **not** activate the TTV model or mark it externally calibrated.

For an eligible bounded TTV v1 case, **My Fit** can:

1. explicitly start a development observation;
2. freeze the candidate range and its non-sensitive model context before the outcome is known;
3. keep the active observation separate from completed calibration evidence;
4. record a documented B2-or-better outcome;
5. calculate observed elapsed weeks automatically;
6. store the completed result as `sample_role=development`;
7. cancel an unfinished observation without creating calibration evidence.

The local calibration store does not contain the full personal profile.

It stores only calibration fields required for evaluation, including:

- anonymous case ID;
- country and remote-employment mode;
- temporal engine/composition versions;
- candidate range and observed weeks;
- frozen start/outcome definition versions;
- optional stage timings;
- bounded context such as starting/target CEFR and study-hours/week.

My Fit also supports a versioned `ttv-development-exchange-v1` JSON package for moving **development** cases between AUGUR installations. The exchange excludes the full profile, direct identifiers, free-text history and local provenance timestamps. Imported exchange cases cannot be promoted retrospectively into holdout evidence.

`check-operability.ps1` reports descriptive calibration diagnostics including:

- development/holdout case counts;
- candidate-interval coverage;
- mean and median interval width;
- mean absolute and signed midpoint error;
- below/above-range miss counts;
- mean miss distance;
- represented CEFR-start and weekly-study-hour cohorts.

CSV import remains available as a compatibility/development path:

```powershell
.\import-ttv-calibration.ps1 -Path ".\my-calibration-cases.csv"
```

These diagnostics remain descriptive. TTV stays unversioned until the external-calibration gate is satisfied on a frozen holdout under a pre-declared protocol and acceptance criteria.

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

Prerequisite:

- import the full official ESCO dataset.

For the current 2025 EURES Annex, AUGUR can now run the complete review pipeline directly from the official ELA PDF:

```powershell
.\build-eures-market-evidence-from-annex.ps1
```

The command:

1. downloads the official ELA Annex PDF unless `-PdfPath` is supplied;
2. extracts the visible grid table with `pdfplumber` rather than OCR;
3. writes `exports\eures_2025_annex_normalized.csv`;
4. writes extraction diagnostics to `exports\eures_2025_annex_extraction.json`;
5. resolves each occupation label against the local full ESCO dataset;
6. requires a configurable match threshold and ambiguity margin;
7. derives the ISCO unit group only from an accepted ESCO match;
8. validates EURES country codes and duplicate ISCO assignments;
9. writes `exports\eures_market_review.json`;
10. keeps ambiguous/unresolved rows explicit;
11. **never modifies** `backend/app/evidence/eures_lmi_2025.json` automatically.

Exit code `0` means both PDF extraction and ESCO review are fully resolved. Exit code `2` means attention is required and production evidence is unchanged.

The lower-level CSV builder remains available for compatibility:

```powershell
.\build-eures-market-evidence.ps1 -Path ".\eures-2025-normalized.csv"
```

The currently reviewed ICT subset remains versioned at:

`backend/app/evidence/eures_shortages_surpluses_2025_ict_normalized.csv`

CI checks that this reviewed table and the production manifest remain identical for those 13 unit groups.

This workflow remains separate from ordinary evidence refresh because the ELA Annex is an annual reviewed evidence source, not a stable machine-readable API.

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
