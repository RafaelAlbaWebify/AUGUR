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
