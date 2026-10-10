# AUGUR — Session Handover

Updated: 2026-10-09. **Read first on resumption, then revalidate live GitHub state.**

## Active task
G3 source/unit/period provenance audit is merged via PR #7 (`aa10370c`). This branch improves uninitialized-database diagnostics and tests. Project-control docs are merged; preserve distinction between code-level CI and actual local-data acceptance.

## Repository snapshot at creation
- PR #7 source/unit/period grouping and orphan-code report merged `aa10370c` after backend/frontend/ops CI passed; real-store acceptance remains pending.
- Main includes PR #1 coverage + exporter, PR #2 geo provenance, PR #3 official GISCO audit.
- PR #4 `feature/compare-official-local-nuts` merged as `ff3766e8`; exact-code comparison now rejects incomplete official catalogs and duplicate local codes. Actual private local matching is still unverified.
- Project-control documents were merged via PR #5 as `9ebe6484`. Documentation-only changes may not trigger path-filtered CI.
- No new numeric completion percentage is justified.

## Known real evidence
- Local geography coverage JSON from user: 26 records; ES/IE/PT only; some historical NUTS2 overlap; OECD not represented in that export.
- Official GISCO catalog job: [37924620862](https://github.com/RafaelAlbaWebify/AUGUR/actions/runs/37924620862), ES NUTS2/3 = 19/59, IE 3/8, PT 9/26.
- Local per-code provenance JSON not yet available; comparing counts is insufficient.
- Existing detailed worklist: [AUGUR_REMAINING_IMPLEMENTATION_2026-10-07.md](AUGUR_REMAINING_IMPLEMENTATION_2026-10-07.md).

## Next actions, in order
1. Confirm PR #5 (project control) and PR #4 (strict code comparison) are merged; recheck GitHub live state before further changes.
2. Inspect actual local per-geography provenance when available; execute exact-code membership against GISCO 2024 and classify historical/unknown codes, rather than assuming count differences are corruptions.
3. Prefer independent GitHub-accessible official-source audits; if local codes are indispensable, request only the smallest necessary export.
4. Confirm versioned boundary membership before altering registration; protect historical observations, and never delete records based solely on count disparity.
5. Validate G3 regional source/unit/period audit: grouped by indicator, source, dataset, unit, temporal range; identify orphaned observation codes. Inspect CI and obtain real-data evidence separately, then continue C1/P1 acceptance.
6. Maintain decision/evidence/handover docs with each milestone. Stop claiming “42% complete”.

## Standard workflow
**Start:** read PROJECT_STATE, ROADMAP, VALIDATION, DECISIONS, HANDOVER → inspect actual main, open PRs, CI, source limitations → choose highest-priority unblocked criterion.

**Build:** coherent milestone-sized implementation, tests, evidence verification, negative paths, documented assumptions → PR.

**Finish:** update current status, evidence, decisions, and exact next action in the same PR; merge after acceptance appropriate to milestone; leave external blockers visible.

**Never** repeat full repository recaps by speculation; use stable documents and live GitHub results.

## G3 source audit evidence — 2026-10-09

Real local ES/IE/PT coverage export was contrasted with configured Eurostat datasets and official dataset descriptions. See [G3 source audit](G3_REAL_SOURCE_AUDIT_2026-10-09.md). Confirmed important qualification: 3/3 ESP NUTS3 registered crime regions is not nationwide coverage; IRL/PRT NUTS2 historical-vintage mixing is suspected but exact codes remain unverified. The comparison establishes source contracts and observation-period discrepancies, **not a completed per-code reconciliation or repair**.

## Master indicator inventory (2026-10-10)

[Master indicator matrix](MASTER_INDICATOR_MATRIX.md) maps economic development, fiscal burden, housing, migration, institutional quality, freedom and living conditions across country/region/city scales. A deterministic generator `backend/scripts/export_indicator_inventory.py` inventories national indicator declarations but does **not** prove source coverage. Product priority shifts to completing P0 fiscal feasibility and actual housing affordability with authoritative source contracts and real observation acceptance. Existing G2/G3 local evidence gaps remain open; no invented readiness percentage.

## 2026-10-10 fiscal scope

PR #10 master indicator matrix merged `42498287`. OECD comparative tax-wedge contract added on `feature/oecd-tax-wedge-contract`, with fixed OECD `DSD_TAX_WAGES_COMP@DF_TW_COMP` v2.1 and single/no-children/100% average-wage scenario. This contract does **not** import tax observations or calculate personalized net pay. Next: verify actual SDMX country responses and integrate source-backed series without inferring tax residency or personal liability. Maintain separate housing and personal tax workstreams.

## OECD fiscal ingestion progress (2026-10-10)

Added `app/ingestion/oecd_tax_wedge.py` to fetch OECD SDMX CSV and normalize only exact AV_TW / S_C0 / AW100 / _Z / annual scenario; isolated negative tests reject conflicting dimensions and do not manufacture missing values. **IMPORTANT:** OAuth-free actual CSV schema/headers and 2025 values have not been directly verified from the runtime; CI tests use contract fixtures. The OECD Data Explorer identifies source v2.1 and the selected query, but a live CSV smoke is required before enabling persistence or calling this product-ready. No automatic sync yet. Next: run external live smoke on GitHub Actions and reconcile column names with actual SDMX response, then wire dataset storage/API/UX.

## 2026-10-10 OECD live-source failure

PR #11 merged as `06e9d001`, with CI green. The automatically triggered official OECD source smoke [38044329238](https://github.com/RafaelAlbaWebify/AUGUR/actions/runs/38044329238) failed with HTTP 500 on the broad tax-wedge query. This is **not** a validated observation ingest. Current branch `fix/oecd-tax-wedge-live-query` switches to three country-specific requests and tests assembly without generating data. Re-run live smoke after merge. If source still returns 500, classify upstream outage/API selection incompatibility; do not mark the fiscal indicator ready.

## OECD fiscal source milestone — 2026-10-10

Actual OECD source smoke [38044771570](https://github.com/RafaelAlbaWebify/AUGUR/actions/runs/38044771570) **passed** after schema correction, reporting exactly six genuine ESP/IRL/PRT 2024/2025 records. PR #13 merged as `349ab1ba`. Registered `oecd_tax_wedge_average_wage` in the national catalog and added an explicit local sync script, which verifies all three country responses before writing and does not fabricate missing data. The script is **not yet executed against the user's local database**, and personalized tax/net income remains future work. Next: validate persistent storage in CI, confirm country-level UI exposure, then expand to net earnings and housing affordability. The indicator is not a personal tax rate.

## Housing evidence contract (2026-10-10)

Regional responses now expose a separate housing-affordability evidence block: Eurostat regional housing-cost-overburden proportion (`ilc_lvho07_r`) and disposable income per person in PPS (`nama_10r_2hhinc`), each preserving source and observation period. No market rent or net-income ratio is fabricated; `affordability_complete=false` until official actual rent/net cash-income series align by territory and time. Tests cover mismatched units and stale-period separation. CI and real local data acceptance are distinct.

## World expansion compatibility — 2026-10-10

[Global expansion contract](GLOBAL_EXPANSION_CONTRACT.md) introduces country-agnostic evidence compatibility checks and an explicit coverage matrix by indicator, provider, geographic level/system, and period. This is a reusable guardrail, not automatic world ingestion. New country onboarding is **not accepted** until official geography/source discovery, ingestion adapter compatibility, observed data and country+region+city acceptance are proven. Next priority: migrate source-specific ingest orchestration and test an actual non-EU country/region/city. No invented worldwide completion estimate.

## Global contract integration — 2026-10-10

The OECD regional **population-density** sync now checks the actual normalized observations against the reusable source/unit/geography contract **before DuckDB writes**. Regression tests include an OECD Australian TL2 row and a rejected boundary-system mismatch. This is a first production-path integration, **not** general worldwide onboarding or proof of fresh Australian observations from the live provider. Next migrate other OECD indicators and Eurostat adapters and run a live non-EU regional/city acceptance without assuming geographic coverage.

## OECD global ingestion guard rollout — 2026-10-10

Beyond density (PR #17), all other OECD regional sync methods (population, safety, demography, labour, GDP, income, broadband and land temperature) now invoke the common country-independent validation before writing observations. Tests verify Australian OECD TL2 rows and reject mismatched datasets, geography systems, non-finite values and missing country IDs. These guards do not establish authoritative world geography completeness or live OECD coverage outside validated pilots. Subsequent work must strengthen source-specific indicator/unit allowlists and validate live non-EU responses.

## OECD global metric allowlist — 2026-10-10

The OECD regional common guard is now **fail-closed** on nine explicit dataset-to-indicator-to-unit mappings; previously it instantiated contracts from the observation's own indicator/unit, allowing incorrect self-consistent values. The change remains country-agnostic, accepts correctly sourced non-EU territory rows, rejects unknown dataset/indicator, wrong unit, and cross-dataset substitution before DuckDB writes. This protects ingestion semantics but does **not** substitute for live non-EU end-to-end acceptance. Eurostat-specific datasets and global country/city discovery remain separate work.

## Eurostat regional evidence validation — 2026-10-10

The explicit source/dataset/unit/indicator guard is now called before DuckDB upsert in the Eurostat **regional housing and labour CLI syncs**. A valid Bulgarian NUTS2-shaped region passes the contract without ES/PT/IE-specific assumptions; wrong units, unexpected metrics, invalid values, or levels fail closed. This is scoped to these two CLI paths and does not modify the existing pilot-country filtering in the upstream normalizer. NUTS vintage is **not inferred from code shape** and still requires official catalog comparison. Remaining: centralize validation across all Eurostat write paths and remove pilot-only discovery restrictions with explicit input eligibility.

## Eurostat configurable country scope — 2026-10-10

Regional housing and labour ingest scripts support `--countries BG FR` (ISO2) while keeping ES/PT/IE as default pilot. The common JSON-stat normalizer now distinguishes omitted selection (pilot) from an explicit empty set (no rows) and rejects invalid ISO2-like prefixes. This enables reusable NUTS2 ingestion across available Eurostat areas without a per-country code change. It does **not** establish official NUTS vintage, complete NUTS territory registration, or country/city coverage; the provider's actual availability remains authoritative. Run from `backend/`: `python -m scripts.sync_eurostat_regional_housing --countries BG FR` or corresponding labour script. Next integrate dynamically verified official geography catalog and source-specific coverage reports.

## Eurostat dataset territory discovery — 2026-10-10

Added read-only `python -m scripts.discover_eurostat_regions --output /path/to/coverage.json` from `backend/`. It queries all four configured regional labour/housing datasets, enumerates published four-character NUTS2-shaped geography candidates by country, and preserves per-source error states and source update times. This works beyond ES/PT/IE without editing code. **Dataset membership is not certification of current NUTS vintage nor proof of nonmissing values or complete EU regional registry**. Next gate: compare against authoritative Eurostat NUTS version/registry and detect observed coverage at country/region level before automatic ingest; do not onboard using code shape alone.

## Eurostat true observation coverage — 2026-10-10

Dataset region membership is now differentiated from actual finite numeric observations in the Eurostat read-only discovery report. The parser maps JSON-stat flattened values using dimension order/size, treats numeric zero as an observation, excludes null/bool/nonfinite values and reports observed regions separately from listed regions. Coverage is restricted to the selected dataset/filters/time periods, not official NUTS completeness or latest series reliability. Real official NUTS vintage reconciliation and live dataset smoke remain outstanding.

## Official GISCO NUTS 2024 reconciliation — 2026-10-10

The read-only Eurostat geography discovery CLI now supports `--reconcile-nuts2024`, fetching GISCO NUTS2 2024 GeoJSON and annotating each dataset region's official-vintage membership separately from finite-value availability. A PR-triggered live official registry smoke validates actual GeoJSON fields and country coverage before merging. This **does not** assert that a historical observation was collected under 2024 boundaries or establish equivalence between vintages. Non-registry codes remain visible as unmatched; errors fail closed. This is GISCO NUTS-only; global cities and non-European geographic systems require their own authoritative registries.

## Live Eurostat regional coverage gate — 2026-10-10

A read-only CI smoke now queries all four configured Eurostat NUTS2 labour/housing datasets, reconciles dataset membership and finite numeric observations against the official GISCO NUTS 2024 registry, and fails closed if any configured dataset is unavailable or has zero observed official NUTS2 2024 regions. Historical/non-2024 codes remain reported separately, including whether they still carry numeric observations; they are not deleted or silently reclassified. **Acceptance depends on the first live workflow result; implementation alone is not real-source validation.**

### Live acceptance evidence — run 38063341094

The live source gate passed against real Eurostat and GISCO responses. GISCO exposed 299 official NUTS2 2024 codes. Dataset results: `nama_10r_2hhinc` 259 published / 250 observed / 250 observed official-2024; `ilc_lvho07_r` 217 / 217 / 214; `lfst_r_lfe2emprt` 351 / 351 / 290; `lfst_r_lfu3rt` 351 / 350 / 289. The housing-overburden source still has observed historical Portuguese codes `PT16`, `PT17`, `PT18`; both labour datasets also expose 61 observed non-2024 codes, including historical IE/PT/HR/HU/LT/NL/NO/SI codes and UK NUTS codes. This proves that source membership cannot be used as a current-region registry. Automatic current-region onboarding must therefore be gated by an authoritative vintage, while historical observations remain visible and must not be deleted merely for failing NUTS 2024 membership. Live workflow: https://github.com/RafaelAlbaWebify/AUGUR/actions/runs/38063341094

## NUTS observation-vintage write safety — 2026-10-10

The live Eurostat/GISCO reconciliation exposed a semantic storage risk: a NUTS-shaped observation without explicit boundary metadata was previously defaulted to `NUTS_2024`. This is not justified by code shape or by current registry membership. The write path now stores such observations as `NUTS_UNSPECIFIED` and does not let them manufacture a current geography-registry row. GISCO-driven syncs register current NUTS2/NUTS3 territories independently as `NUTS_2024`. Current registered territories may use same-code `NUTS_UNSPECIFIED` observations for analytical coverage, but reads expose `same_code_vintage_unverified` rather than claiming the observation used 2024 boundaries. Existing historical rows are not deleted.
