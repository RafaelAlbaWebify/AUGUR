# AUGUR Architecture

## Purpose

AUGUR is a local-first analytical application for country trajectory, scenario exploration, comparison, and eventual personal viability analysis.

## Analytical pipeline

```text
Official/public source
        ↓
Provider adapter
        ↓
Normalized observation
        ↓
DuckDB analytical store
        ↓
Canonical source selection + evidence quality
        ↓
Historical trend engine
        ↓
Dimension synthesis
        ↓
Official outlook
        ↓
AUGUR scenario envelope
        ↓
Personal Fit / TTV
```

Each stage consumes the output of the previous stage. Forecasts are kept out of historical trend calculations, and personal-fit preferences are kept out of country facts.

## Provider registry

Core providers are registered in `backend/app/providers.py`.

A provider declares:

- provider ID and label;
- adapter factory;
- country support predicate;
- sync function;
- optional shared-payload preparation hook.

The registry currently contains:

- World Bank
- Eurostat
- OECD
- IMF
- UN World Population Prospects

`sync_core.py` no longer knows source-specific implementation details. It asks the registry which providers support a country and runs them.

This is intentionally lighter than a runtime plugin marketplace. AUGUR uses trusted first-party provider adapters rather than arbitrary executable third-party extensions.

## Storage

### DuckDB

Analytical data:

- countries
- sources
- indicators
- observations

Observation identity:

`country + indicator + period + source`

### SQLite

Application/profile/settings state and local personal-fit inputs.

## Backend

FastAPI exposes country evidence and analytical services.

Key API families:

- country registry
- current snapshots
- historical trends
- dimension assessment
- source evidence quality
- official forecasts
- future trajectory horizons
- AUGUR scenarios
- multi-country comparison
- personal profile readiness
- LegalFit, LanguageFit, CareerFit and FinancialFit
- TTV dependency readiness

## Frontend

React + TypeScript + Vite.

Current major views:

- routed Overview dashboard
- routed Indicators evidence view
- routed Dimension Detail drill-down
- local-first world view
- Personal Fit snapshot and Profile
- official outlook
- scenario envelopes
- country comparison
- guarded persistent Edit Layout controls

The map uses bundled Natural Earth geometry through `world-atlas`; it does not require a tile API or API key.

## Testing

### Backend

Pytest covers:

- catalog invariants
- trend interpretation
- dimension synthesis
- source adapters
- scenario logic
- provider routing
- comparison alignment
- source-quality query contract

### Frontend

Production TypeScript/Vite build runs in CI.

Playwright smoke tests mock the API contract and verify:

- routed analytical sections render;
- country switching works without reload;
- comparison stays aligned and neutral;
- world-view navigation drives country selection;
- Profile inputs, completion, evidence, outputs and TTV remain distinct;
- Edit Layout cannot hide core panels or break approved proportions;
- desktop, tablet and mobile layouts avoid horizontal overflow.

This makes UI validation deterministic and independent of third-party source availability.

## CI

GitHub Actions runs on pushes and pull requests:

1. backend dependency install + pytest;
2. frontend dependency install + production build;
3. Chromium installation;
4. Playwright browser smoke suite.

## Local ports

- frontend: 5190
- backend: 8020

These are intentionally isolated from the other local Webify projects.


## Personal Fit pipeline

Personal Fit is downstream of country evidence.

Current dependency chain:

```text
Local profile
    ↓
LegalFit
LanguageFit
CareerFit
FinancialFit
    ↓
TTV dependency readiness
```

TTV is not an aggregate score. It remains blocked whenever a required evidence layer is incomplete.

CareerFit combines broad EURES labour-market signals with locally loaded ESCO occupation/skill evidence. Full ESCO CSV packages can be imported into SQLite; seed mode is deliberately partial and never marks skill evidence complete.

Occupation resolution is explicit and confidence-gated. Low-confidence ESCO candidates are exposed but not silently selected.


## Operability state

Runtime health and analytical operability are separate concepts.

`/api/health` answers whether the local application datastores are technically available.

`/api/operability` evaluates whether AUGUR has enough evidence to be used as intended. It checks:

- observed and official-forecast evidence for every registered country;
- coverage of every provider configured for that country;
- provider retrieval freshness;
- Eurostat labour-earnings evidence;
- full ESCO occupation/skill/relation coverage;
- availability of a validated TTV temporal model.

Provider synchronization older than 30 days is considered stale by the current operational policy. This tests whether the local cache has been refreshed recently; it does not require each source's statistical observation year to be within 30 days.

AUGUR reports analysis readiness separately from full product readiness. The product can therefore be analytically useful while still refusing to publish a TTV duration.
