# AUGUR — Validation and Evidence Register

Updated: 2026-10-09. **A green test is only a tested behavior; it is not a real-data acceptance certificate.**

| Capability | Implementation evidence | CI / automated evidence | Real-data evidence | Product acceptance |
|---|---|---|---|---|
| Geographic indicator coverage | PR #1, merged `cd2bfbf` | Green PR CI + merge CI | Local JSON of 2026-10-09: 26 rows across ESP/IRL/PRT; version mismatch concerns | **Pending** |
| Per-geography local provenance | PR #2, merged `c2392e3` | Green CI | Export has **not** been provided | **Pending** |
| Official GISCO 2024 code catalog | PR #3, merged `61e7028` | Official workflow run [37924620862](https://github.com/RafaelAlbaWebify/AUGUR/actions/runs/37924620862) succeeded and uploaded artifact | Actual GISCO 2024 retrieval: ES 19/59, IE 3/8, PT 9/26 (NUTS2/NUTS3) | Catalog retrieval accepted; matching to local **pending** |
| Local-to-official code comparison | PR #4 merged `ff3766e8` | CI green incl. negative tests for malformed catalog and duplicate local codes | No joined local data result yet | **Pending** |
| G3 observation provenance inventory | PR #7 merged `aa10370c`, read-only service + JSON exporter | CI green: source/unit separation, unregistered geo detection; missing-schema regression test added in following PR | Actual local store not yet audited with this export | **Pending** |
| Frontend country journey | Existing Playwright mocks and UI audit | Mocked browser suite green on reviewed PRs | No full fresh-real-data walkthrough accepted here | **Pending** |
| TTV prediction publishing | Bounded model and tests per existing TTV docs | Existing automated tests | Prospective representative holdout not verified | **Blocked** |

### Key methodological hazards
1. Local registered-code denominator is **not** provider's official geographical universe.
2. Latest imported period of each geography is **not** same-year availability.
3. Actual `retrieved_at` reflects *ingestion*, not publication age of source.
4. Historical NUTS codes with 2011/2018 end periods cannot be relabeled “current 2024” without source version audit.
5. Comparing exact codes does not by itself establish boundary/indicator methodological comparability.
6. OECD regional/FUA series and Eurostat NUTS/Urban Audit are different geographic systems; do not merge silently.
7. Counts from GitHub official catalog job represent **catalog identities**, not observed stats.

### Acceptance evidence for new work
- Code/PR and changed paths; automated test URL/commit; actual provider or local evidence reference; schema and provenance checks; negative/empty cases; explicit unresolved limitations; reviewer decision.
- For local-only evidence, record that a human supplied export was inspected; never claim GitHub Actions validated the local database.
- A failed real-world command is a defect signal even if CI was green. Example: first geography export failed on an uninitialized schema; initialization resolved it locally; consider schema preflight UX separately.

## G3 source audit evidence — 2026-10-09

Real local ES/IE/PT coverage export was contrasted with configured Eurostat datasets and official dataset descriptions. See [G3 source audit](G3_REAL_SOURCE_AUDIT_2026-10-09.md). Confirmed important qualification: 3/3 ESP NUTS3 registered crime regions is not nationwide coverage; IRL/PRT NUTS2 historical-vintage mixing is suspected but exact codes remain unverified. The comparison establishes source contracts and observation-period discrepancies, **not a completed per-code reconciliation or repair**.

## OECD fiscal source milestone — 2026-10-10

Actual OECD source smoke [38044771570](https://github.com/RafaelAlbaWebify/AUGUR/actions/runs/38044771570) **passed** after schema correction, reporting exactly six genuine ESP/IRL/PRT 2024/2025 records. PR #13 merged as `349ab1ba`. Registered `oecd_tax_wedge_average_wage` in the national catalog and added an explicit local sync script, which verifies all three country responses before writing and does not fabricate missing data. The script is **not yet executed against the user's local database**, and personalized tax/net income remains future work. Next: validate persistent storage in CI, confirm country-level UI exposure, then expand to net earnings and housing affordability. The indicator is not a personal tax rate.

## Housing evidence contract (2026-10-10)

Regional responses now expose a separate housing-affordability evidence block: Eurostat regional housing-cost-overburden proportion (`ilc_lvho07_r`) and disposable income per person in PPS (`nama_10r_2hhinc`), each preserving source and observation period. No market rent or net-income ratio is fabricated; `affordability_complete=false` until official actual rent/net cash-income series align by territory and time. Tests cover mismatched units and stale-period separation. CI and real local data acceptance are distinct.

## Global contract integration — 2026-10-10

The OECD regional **population-density** sync now checks the actual normalized observations against the reusable source/unit/geography contract **before DuckDB writes**. Regression tests include an OECD Australian TL2 row and a rejected boundary-system mismatch. This is a first production-path integration, **not** general worldwide onboarding or proof of fresh Australian observations from the live provider. Next migrate other OECD indicators and Eurostat adapters and run a live non-EU regional/city acceptance without assuming geographic coverage.

## OECD global ingestion guard rollout — 2026-10-10

Beyond density (PR #17), all other OECD regional sync methods (population, safety, demography, labour, GDP, income, broadband and land temperature) now invoke the common country-independent validation before writing observations. Tests verify Australian OECD TL2 rows and reject mismatched datasets, geography systems, non-finite values and missing country IDs. These guards do not establish authoritative world geography completeness or live OECD coverage outside validated pilots. Subsequent work must strengthen source-specific indicator/unit allowlists and validate live non-EU responses.

## OECD global metric allowlist — 2026-10-10

The OECD regional common guard is now **fail-closed** on nine explicit dataset-to-indicator-to-unit mappings; previously it instantiated contracts from the observation's own indicator/unit, allowing incorrect self-consistent values. The change remains country-agnostic, accepts correctly sourced non-EU territory rows, rejects unknown dataset/indicator, wrong unit, and cross-dataset substitution before DuckDB writes. This protects ingestion semantics but does **not** substitute for live non-EU end-to-end acceptance. Eurostat-specific datasets and global country/city discovery remain separate work.

## Eurostat regional evidence validation — 2026-10-10

The explicit source/dataset/unit/indicator guard is now called before DuckDB upsert in the Eurostat **regional housing and labour CLI syncs**. A valid Bulgarian NUTS2-shaped region passes the contract without ES/PT/IE-specific assumptions; wrong units, unexpected metrics, invalid values, or levels fail closed. This is scoped to these two CLI paths and does not modify the existing pilot-country filtering in the upstream normalizer. NUTS vintage is **not inferred from code shape** and still requires official catalog comparison. Remaining: centralize validation across all Eurostat write paths and remove pilot-only discovery restrictions with explicit input eligibility.
