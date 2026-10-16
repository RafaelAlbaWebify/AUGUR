# GR-0 — Current Geographic Ranking Readiness Audit

Date: 2026-10-16. **Status: code-path audit complete; actual current local DuckDB observation export pending.** This is not ranking feature acceptance.

## Existing system and reuse decisions

| Function | Existing code / endpoint | Assessment |
|---|---|---|
| National comparison | `frontend/src/components/ComparePanel.tsx`; `GET /api/compare` | Country ISO3 selector and indicator comparisons exist; frontend has three slots, API allows up to five |
| City evidence | `frontend/src/components/OverviewPage.tsx`; `GET /api/cities/{city_code}/evidence` | Detailed urban evidence available for supported stored city codes, not a city ranking |
| Region evidence | `OverviewPage.tsx`; `/api/regions/{geo_code}/evidence`, `/api/geographies/{geo_code}/evidence` | Existing source-specific region details; retain geographic system |
| Regional comparison | `OverviewPage.tsx`; `GET /api/geographies/compare` | Two same-system, same-level geographies from the selected country's catalog; no general 1–3 cross-country picker |
| Catalog | `GET /api/geographies?country_iso3=...`, `geography_registry` | Reuse; unambiguous stable IDs and boundary contracts needed |
| Coverage | `/api/geographies/coverage/indicators`; `geography_indicator_coverage.py` | Already reports registered coverage and same-period counts; does not group source/unit/dataset |
| Provenance | `geography_provenance.py`, exporter | Registered identities, sources and datasets; not observation-level source/unit/year rows |
| Defined metrics | `export_indicator_inventory.py` | National indicator declarations only; not proof of actual values |

## GR-0 minimal addition

`backend/scripts/export_ranking_evidence_audit.py` produces a JSON summary of **stored** national and registered subnational observation groups by country, geography system/level, indicator, exact year, unit, source and dataset. It connects read-only to DuckDB and does not export individual values or modify persistent data.

Local execution (from the existing one-and-only AUGUR checkout):

```powershell
Set-Location "$HOME\Documents\GitHub\AUGUR\backend"
.\.venv\Scripts\python.exe -m scripts.export_ranking_evidence_audit --countries ESP PRT IRL --output "$HOME\Downloads\AUGUR_GR0_RANKING_EVIDENCE.json"
```

Output fields include national and subnational observation groups and registered group denominators. The local evidence export is required to confirm **today's** data: no GitHub checkout has access to the user's persistent local DuckDB.

## Known evidence caveats

- G3 audit 2026-10-09 found ESP NUTS2 regional income/health/housing data incomplete (only four of nineteen registered for several series in the then-current snapshot); do not infer the latest local database remains at those counts.
- Some Irish city population observations were 2011/2016; a city registry or historical observation does not establish current city rankings.
- Historical Irish and Portuguese NUTS codes were present before the G2 reconciliation; a correct registry code does not prove every observation's boundary vintage.
- One provider year, unit and source per geography still does not establish internationally harmonized indicator meaning; GR-1 must gate methodologically valid comparisons.

## Candidate metrics for GR-1 evaluation (not yet accepted)

| Candidate | Location level | Evidence to verify in local export | Potential blocker |
|---|---|---|---|
| Unemployment rate | National / NUTS2 | Same-year cross-country coverage, compatible Eurostat source and unit | Old geographic vintage and mismatched periods |
| Employment rate | National / NUTS2 | Population denominator and age bracket match | Indicator semantic divergence |
| Household disposable income | National / NUTS2 | Comparable PPS per capita and same periods | Incomplete regional coverage and source dimension contracts |
| Housing cost overburden | NUTS2 | Actual common-year recorded values and regional scope | Limited observed countries/regions and methodology |
| City population | Urban Audit city | Same city definition/vintage and common year | Stale urban observations; not affordability |
| Actual city house purchase price | City | Find real source-backed, compatible observed series | No accepted cross-country city price observation established yet |
| Occupation-specific city jobs | City | Verifiable occupation+city coverage, period and provenance | Not yet proven from current provider data |

## GR-0 acceptance checkpoint and GR-1 handoff

**Verified now:** existing paths, source schema (`observations`, `subnational_observations`, `geography_registry`), missing rank API and the existing G3 exporter limitations. **Not yet verified:** present local counts by source/unit/period and any eligible cross-country city ranking.

Next: (a) CI-test the read-only exporter; (b) inspect user's sanitized JSON export when available; (c) enumerate candidate rankable same-year source+unit cohorts and flagged exclusions, leading to GR-1 comparability contract. Do not start public ranking UI with misleading sample numbers.

## Real local export results — 2026-10-16 (GR-0 observation gate)

Evidence artifact: operator-supplied `AUGUR_GR0_RANKING_EVIDENCE.json`, generated from persistent local DuckDB with the read-only exporter. **This artifact is user-local, not checked into GitHub**. Counts below are stored rows/registered evidence, not official provider-universe completeness or semantic approval.

- Countries: ESP, PRT, IRL. **29 distinct national indicator IDs**, **21 distinct registered subnational indicator IDs**; 4,491 national aggregate groups and 488 subnational aggregate groups from this export. Aggregated groups are not equivalent to unique locations or values.
- Registered Urban Audit cities: ESP 112, PRT 16, IRL 5; registered NUTS2024 level-2 geographies: ESP 19, PRT 9, IRL 3.
- Exact 2025 same-year NUTS2024/EUROSTAT cohorts: `regional_unemployment_rate` / `lfst_r_lfu3rt` / percent: ESP 19, PRT 9, IRL 3 = **31**; `regional_employment_rate` / `lfst_r_lfe2emprt` / percent: ESP 19, PRT 9, IRL 3 = **31**. These are the GR-2 pilot candidates, conditional on GR-1 methodological/vintage validation.
- Cross-country Urban Audit city `city_population` / `urb_cpop1` / persons / 2024: ESP 112 + PRT 16 = **128**; Ireland has no 2024 city cohort in the export. `city_median_age` / `urb_cpopstr` / years / 2023: ESP 92 + PRT 16 = **108**. Descriptive city rankings only; not a proxy for cost of living or job opportunity.
- Irish city population records are historical (latest 2016 in this scope). NUTS_UNSPECIFIED legacy observations persist for IRL/PRT; do not silently mix vintages.
- Some national records extend beyond 2026 while labelled `observation_type=observed` (UN_WPP and/or IMF time horizons). **GR-1 must explicitly separate projection/forecast series from historical observations**, irrespective of the stored label, and not accept a future period in the observed-only ranking.
- The export contains counts, units, years, dataset names and source IDs, **not numerical values**. Therefore an independently reproduced ordering and final national/regional/city ranking **remain unaccepted** until the ranking query is run against local observations and source meaning verified.
- No verified harmonized city house purchase price, city occupation-specific vacancy, or city disposable income ranking demonstrated by this export.

**Next:** GR-1 eligibility/comparability contract and tests (especially geographic vintage, official dataset semantics, future-year status); then implement GR-2 for the verified 2025 regional pilot. GR-0 code-path + local evidence inventory achieved; the statistical comparability acceptance gate remains explicit.
