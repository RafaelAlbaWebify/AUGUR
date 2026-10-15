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

## Legacy NUTS_2024 local audit — 2026-10-10

Added `python -m scripts.audit_legacy_nuts_vintage --output <file.json>`, a read-only operator audit for databases that may contain rows written before the implicit-vintage fix. It checks locally stored `NUTS_2024` NUTS2/NUTS3 observation groups and registry rows against live GISCO NUTS 2024. A code absent from GISCO is classified as a definite invalid current-vintage claim; a code present in GISCO remains `code_current_observation_vintage_unverified` because code membership alone cannot certify historical boundaries. The tool performs no mutation. Actual G2 local acceptance still requires running it against the user's persistent DuckDB and reviewing the generated JSON.

## Next session handover — 2026-10-13

G2 local reconciliation and application data-layer acceptance finished and adopted with rollback backup. Full G2 details in ROADMAP/VALIDATION. Latest merged UI PR #33 removed redundant Country Radar copy and added hover help; CI green, fresh local visual acceptance pending. Next highest priority: G3 real source/unit/period audit on current local store; reuse existing G3 provenance exporter rather than inventing another standalone verification module. Do not repeat the 18-table diff or historical NUTS correction. Product launch status remains partial only due to externally gated TTV, with analysis readiness separately assessed.

## Active Country Radar follow-up — 2026-10-13

PR #42 merged. Local three-country screenshot audit identified mainland framing issue for ESP and PRT due to country bounds including archipelagos; IRL layout acceptable. Repair planned as camera-only defaults, preserving all geometries and data, with explicit browser zoom/center contract and renewed real-browser acceptance. No local DuckDB migration, setup, or extra worktree required. G3/C1 product acceptance remains pending; do not mistake GitHub CI for visual acceptance.

## Country Workspace v2 implementation checkpoint — 2026-10-13

A feature branch `feature/configurable-country-workspace-v2` now contains a three-pane desktop grid with bounded live width controls, browser-local persistence and reset; original country, regional evidence and map data paths are retained. A Playwright regression for pane ordering and persistence has been added. This is **implementation only**: no local TypeScript build, full Playwright preflight, CI, or real-world visual acceptance has been completed. Direct-grab, keyboard-accessible splitters have since been implemented along with the width sliders, but have not passed a real-browser preflight yet. Visibility controls, indicator selection/order, and presets remain unimplemented; do not merge or claim that the configurable workbench is complete. The next step is to validate/refine layout against 1650×900 and actual ESP/PRT/IRL regional journeys before publishing a release candidate.

## Workspace v2 local preflight evidence — 2026-10-14

Operator ran frontend build successfully on Windows (`tsc -b && vite build`). Initial four-worker Playwright attempt timed out during browser startup, not a demonstrated UI assertion failure. Subsequent correct direct Playwright invocation with one worker and 90-second per-test timeout passed all 4 selected desktop checks (1650×900, 1920×900, 1920×1080, and resize/persistence/reset), 3.2 minutes; evidence archive `AUGUR_TEST_20261014_201934.zip` contained `playwright.log` and `.last-run.json`. No success-run screenshots were produced because the test suite uses failure-only screenshots. This verifies these four mocked-browser contracts only; full suite, actual ESP/PRT/IRL data selection and visual approval are not yet accepted. Local npm audit reported one high-severity issue, pending dependency identification/triage. Do not merge until follow-up checks and visual acceptance.

## Workspace v2 screenshot review — 2026-10-15

Operator supplied `AUGUR_VISUAL_20261015_094016.zip`, containing two passing-test screenshots at 1650×900 and 1920×900. The two-row metric grid fits, and the three panes are separated; however, visual acceptance **failed**: mocked map displays synthetic rectangle geometries (not real national boundaries), the map's Europe/Focus controls were partly clipped due to 290px map height inside a 350px panel with extra headers, right-hand evidence is displaced by Recent Changes when no region selected, the full-size decorative country image dominates the left column, and signals are too small. Screenshot fixture also reports 0 integrated geographies/13 indicators, which are mocks and not evidence of missing actual local ESP/PRT/IRL data. Added corrective CSS for the overflowing map viewport and signal typography plus Playwright assertion that both map action buttons stay inside the panel. These changes remain unvalidated. Next: revise composition toward approved mockup (persistent right evidence panel, compact country summary, recent changes in left pane), capture fresh screenshots, test country-region flows against actual local database, audit npm issue and full suite. No PR or main merge yet.

## Workspace v2 composition update — 2026-10-15

Country Radar was structurally recomposed in the feature branch: country summary and Recent Changes/strengths/risks now occupy the left column, map center, dedicated geographic evidence right. Before selection the right panel explicitly says no geography selected, with country-specific integrated-coverage count (no fabricated data); after selection existing real regional/city evidence remains in the right panel. Left signal panel scrolls internally rather than stretching the page; responsive and desktop tests were updated for the new composition. This is committed source, NOT yet built or visually accepted. Prior mocked-map screenshot geometries are fixtures, not evidence that live geographic shapes are rectangles. Full preflight, actual ESP/PRT/IRL evidence checks and npm audit follow-up remain gates; do not merge.

## 2026-10-15 visual acceptance retry

Operator build TypeScript/Vite PASSED. 2 focused Workspace v2 Playwright tests: baseline 1920x900 capture PASSED; resize test FAILED because its third-panel selector `.recentChangesPanel` now points to the intentionally relocated left-side changes panel, not the right evidence pane. Screenshot confirmed three columns non-overlapping and ten metric cards within frame; country hero synopsis was cropped, right empty placeholder too sparse, mocked GISCO features rectangular (fixture only). Corrected test selectors to target `.countryRadarHero > .geographicEvidencePlaceholder` and increased 900px desktop workspace height to 390px with 166px country hero, scrollable left changes and 267px map canvas. Neither revised test nor visual result has yet been executed. G3 data-country acceptance, npm audit vulnerability and customizable indicator picker remain pending. Keep branch unmerged.

## 2026-10-15 — vertical resize implementation

Operator supplied live Spain screenshots confirming horizontal width sliders work and explicitly requested vertical adjustment. Workspace v2 now stores `height` (310–580 px, default 390) alongside left/right panel widths, adds a visible horizontal bottom drag handle and keyboard arrow operation, plus a header Height slider and Reset layout for all three dimensions. Desktop grid, map canvas and evidence panel heights are bound to the persisted size, replacing the previously hard-coded 350/390px values. Playwright test includes height adjustment, persistence, keyboard and reset. These commits have not yet been built, browser-tested, or visually accepted on the local operator installation. Main untouched. Next verify with real browser and visually inspect region-selected state before any PR.

## Dock workspace architectural prototype — 2026-10-15

User rejected linked column heights and requested Windows-like independently sized/movable/hideable widgets. On existing feature branch, introduced separate persisted widget settings `augur.dockWidgets.v1` (width, height, visible, order) for country, recent changes, map, evidence. Added widget toolbar for hide/re-add/reset, per-widget size sliders, header drag-to-swap and keyboard-accessible move buttons, plus initial Playwright coverage. Reused existing data/region state and retained prior layout preferences for now. THIS IS AN UNVALIDATED IMPLEMENTATION CHECKPOINT, NOT A COMPLETE OR ACCEPTED DOCKING RELEASE. Existing legacy CSS constraints and tests must be reconciled, complete local TypeScript/Vite and browser suite executed, resizing in both axes tested visually against live regional data, and indicators/grid converted to optional widgets before merging. No PR/merge to main. A purpose-built grid/docking library may supersede current flex-based positioning once compatibility and test coverage are established.

## Dock consolidation and indicator configurability — 2026-10-15

Current feature branch includes individually persisted width/height/visibility/order for four dock widgets, drag-to-swap headers, restore windows, and a separate persisted country-indicator category visibility picker. User requested Windows-style independence; the current model uses flex-wrap and widget-level controls, NOT a fully featured freely draggable/floating Windows layout. Legacy desktop width/height header sliders are hidden in desktop docking mode to avoid conflicting controls. Added one Playwright regression for indicator visibility/reset; existing three-pane workspace tests now require revision or retirement in dock mode. All latest changes are unverified by build, CI, browser, or real local visual screenshots. Do not merge or claim operability acceptance. Next action is targeted preflight in an isolated clean frontend environment, reconcile old tests and geometry, inspect operator screenshots, then add per-indicator (not just per-category) selection and tile reordering.

## 2026-10-15 — dock regression consolidation

Replaced the obsolete Playwright contract for linked Country/Evidence/Height sliders with a dock preference persistence test and changed the 1920x900 no-overlap assertion to geometry-based collision checking rather than fixed panel order. Preserved existing tests for independent map dimensions, hide/re-show, reordering, and indicator selection. These test edits are committed but unexecuted; full TypeScript build, mock-browser test suite, real-data visual inspection and package audit remain pending. Do not merge this branch on the basis of source-only checks.

## 2026-10-15 — PR #44 browser CI triage

The first draft PR CI run 38725117093 completed: backend PASS, ops-scripts PASS, frontend 80/86 Playwright PASS (6 FAIL). Failures diagnosed from real frontend job logs: ambiguous navigation Indicators vs Manage indicators; ambiguous New South Wales match due nested comparison; old fixed 900px all-cards-visible viewport expectation incompatible with user-adjustable taller layout; recent-changes clipping assumption incompatible with scrollable widget; two legacy `.recentChangesPanel` selectors ambiguous after evidence panel separation. Commit 4f48b00 updates test assertions/selectors accordingly and triggers new CI run 38726453413. Build and full acceptance of that new run are pending, as is desktop screenshot review and authentic data inspection. PR #44 remains draft, no merge.

## 2026-10-15 — corner resize after green CI

CI 38726662656 completed SUCCESS across frontend, backend, ops scripts after the dock test migration. Added direct per-window bottom-right corner resize controls on country, changes, map, evidence (desktop >=1400px), supporting pointer capture, diagonal resize and keyboard arrows; widths/heights still persist through `augur.dockWidgets.v1`. Introduced Playwright test for map resize grip, keyboard and pointer changes, persistence and isolation of country panel height. This new update is NOT YET CI accepted or visually inspected; keep PR #44 draft. True docking/snap, metrics-as-widgets and per-indicator customization remain unresolved.

## 2026-10-15 — green corner-resize CI and regional indicator picker

GitHub Actions run 38728854874 completed SUCCESS in all three jobs (frontend, backend, ops scripts), covering desktop dock corner resize. Regional metric cards can now be individually shown/hidden using Manage indicators (real loaded regional evidence names), persisted using namespaced `regional:<indicator_id>` keys distinct from national dimension visibility, and reset with Restore all indicators. Added browser test for AU1 New South Wales selection, hide Population density, reload, and recovery. This newest implementation has not yet passed CI or visual acceptance. PR #44 remains draft and unmerged. Known deficits: floating/docking engine, drag-edge snap, indicator card resize/ordering, mobile responsive dock controls, and real-data screenshots.

## 2026-10-15 — indicator card ordering

Added persistent independent card ordering for national country dimension cards and regional indicators via `augur.indicatorOrder.v1`. Manage indicators now includes keyboard-accessible move-earlier/move-later controls and applies CSS `order` to cards, without changing underlying evidence or card click/navigation behavior. Prevented the controls inside checkbox labels from inadvertently toggling visibility. Added Playwright persistence test. Latest changes are not yet CI or visual accepted; PR #44 remains draft. Ordering uses card-level CSS grid order, not free drag-and-drop tiles; true floating docking remains future work.
