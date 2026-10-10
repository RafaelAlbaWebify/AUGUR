# AUGUR — Evidence-gated Roadmap

Updated: 2026-10-09. **No arbitrary completion percentages.** Each milestone is accepted only after criteria are evidenced. Detailed backlog: [AUGUR_REMAINING_IMPLEMENTATION_2026-10-07.md](AUGUR_REMAINING_IMPLEMENTATION_2026-10-07.md).

| ID | Outcome | Status | Acceptance criterion | Next action |
|---|---|---|---|---|
| R0 | Persistent project-control context | In progress | Five coordinating documents published on main and used on every consequential PR | Merge this documentation PR after review/CI |
| G1 | Observable regional coverage | Implemented + CI validated; local evidence partially inspected | Counts are actual stored distinct codes and years; export distinguishes absent data and catalog universe | Preserve real-export provenance and identify exact code mismatches |
| G2 | Official NUTS catalog comparison | Official catalog workflow and comparison code CI validated; real local comparison pending | Official 2024 code set compared *per country/level/code* against stored local provenance, with version mismatches classified; no automatic deletes | Obtain genuine local per-code provenance evidence, compare exact codes and version labels, classify mismatches without deleting history |
| G3 | Source-backed regional/urban indicator completeness | Provenance inventory implemented in branch; real-data acceptance pending | Provider dataset-by-dataset source audit, observed periods, geo versions, units and missingness; UI displays limits | Review ES/PT/IE sparse indicators and OECD evidence separately |
| C1 | General country evidence / insight experience | Implemented in part; real acceptance unrecorded | Documented end-to-end country journeys with authentic synchronized data, error/empty states and consistent citations | Build focused acceptance matrix from existing UI audit |
| L1 | Occupational demand and skill/language evidence | Partial; externally constrained | Clear provider scope, actual occupation-level evidence, provenance, no fabricated skill demand; gated sources left explicitly gated | Review access-gated Skills-OVATE and posting vendor pilot only if defensible |
| P1 | Personal Fit + Financial Fit correctness | Partial; acceptance not established | Realistic profile journeys; legal/language/career/financial dependencies independently verified | Build acceptance scenarios and enumerate blockers |
| T1 | TTV external validation | Externally blocked | Representative prospective untouched holdout meets frozen criteria; version assigned *only if accepted* | Collect/review legitimate holdout; no synthetic substitution |
| O1 | Operability and release qualification | Not accepted | Explicit release-gate matrix, local runtime smoke + data/source audit + regression + blocking issues closed | Define release gates after G2/C1/P1 checks |

**Priority order:** G2 → G3 → C1/P1 → O1. T1 and access-restricted sources run independently; do not pretend their blockers can be solved by repository-only changes.

**Rules:** No invented observations; no forced coverage denominators; no conflation of geographies across boundary vintages; no declaring completion from CI alone. Prefer completing a milestone over accumulating one-file PRs.

## Master indicator inventory (2026-10-10)

[Master indicator matrix](MASTER_INDICATOR_MATRIX.md) maps economic development, fiscal burden, housing, migration, institutional quality, freedom and living conditions across country/region/city scales. A deterministic generator `backend/scripts/export_indicator_inventory.py` inventories national indicator declarations but does **not** prove source coverage. Product priority shifts to completing P0 fiscal feasibility and actual housing affordability with authoritative source contracts and real observation acceptance. Existing G2/G3 local evidence gaps remain open; no invented readiness percentage.

## OECD fiscal source milestone — 2026-10-10

Actual OECD source smoke [38044771570](https://github.com/RafaelAlbaWebify/AUGUR/actions/runs/38044771570) **passed** after schema correction, reporting exactly six genuine ESP/IRL/PRT 2024/2025 records. PR #13 merged as `349ab1ba`. Registered `oecd_tax_wedge_average_wage` in the national catalog and added an explicit local sync script, which verifies all three country responses before writing and does not fabricate missing data. The script is **not yet executed against the user's local database**, and personalized tax/net income remains future work. Next: validate persistent storage in CI, confirm country-level UI exposure, then expand to net earnings and housing affordability. The indicator is not a personal tax rate.

## World expansion compatibility — 2026-10-10

[Global expansion contract](GLOBAL_EXPANSION_CONTRACT.md) introduces country-agnostic evidence compatibility checks and an explicit coverage matrix by indicator, provider, geographic level/system, and period. This is a reusable guardrail, not automatic world ingestion. New country onboarding is **not accepted** until official geography/source discovery, ingestion adapter compatibility, observed data and country+region+city acceptance are proven. Next priority: migrate source-specific ingest orchestration and test an actual non-EU country/region/city. No invented worldwide completion estimate.

## Eurostat configurable country scope — 2026-10-10

Regional housing and labour ingest scripts support `--countries BG FR` (ISO2) while keeping ES/PT/IE as default pilot. The common JSON-stat normalizer now distinguishes omitted selection (pilot) from an explicit empty set (no rows) and rejects invalid ISO2-like prefixes. This enables reusable NUTS2 ingestion across available Eurostat areas without a per-country code change. It does **not** establish official NUTS vintage, complete NUTS territory registration, or country/city coverage; the provider's actual availability remains authoritative. Run from `backend/`: `python -m scripts.sync_eurostat_regional_housing --countries BG FR` or corresponding labour script. Next integrate dynamically verified official geography catalog and source-specific coverage reports.

## Eurostat dataset territory discovery — 2026-10-10

Added read-only `python -m scripts.discover_eurostat_regions --output /path/to/coverage.json` from `backend/`. It queries all four configured regional labour/housing datasets, enumerates published four-character NUTS2-shaped geography candidates by country, and preserves per-source error states and source update times. This works beyond ES/PT/IE without editing code. **Dataset membership is not certification of current NUTS vintage nor proof of nonmissing values or complete EU regional registry**. Next gate: compare against authoritative Eurostat NUTS version/registry and detect observed coverage at country/region level before automatic ingest; do not onboard using code shape alone.

## Live Eurostat coverage acceptance — 2026-10-10

The next G2/G3 evidence gate is automated: execute the four configured Eurostat regional datasets against the official GISCO NUTS2 2024 registry, require real finite observations on current official codes, and retain historical/non-current observed codes as explicit evidence rather than deleting them. A green source workflow establishes provider-response evidence for this dataset/filter snapshot only; it does not prove complete EU coverage or boundary equivalence across vintages.

### Live acceptance evidence — run 38063341094

The live source gate passed against real Eurostat and GISCO responses. GISCO exposed 299 official NUTS2 2024 codes. Dataset results: `nama_10r_2hhinc` 259 published / 250 observed / 250 observed official-2024; `ilc_lvho07_r` 217 / 217 / 214; `lfst_r_lfe2emprt` 351 / 351 / 290; `lfst_r_lfu3rt` 351 / 350 / 289. The housing-overburden source still has observed historical Portuguese codes `PT16`, `PT17`, `PT18`; both labour datasets also expose 61 observed non-2024 codes, including historical IE/PT/HR/HU/LT/NL/NO/SI codes and UK NUTS codes. This proves that source membership cannot be used as a current-region registry. Automatic current-region onboarding must therefore be gated by an authoritative vintage, while historical observations remain visible and must not be deleted merely for failing NUTS 2024 membership. Live workflow: https://github.com/RafaelAlbaWebify/AUGUR/actions/runs/38063341094

## Boundary-vintage separation — 2026-10-10

Current territorial membership and observation boundary vintage are now separate concerns. GISCO is the authority for current NUTS 2024 membership. Eurostat observations that do not declare a boundary vintage remain `NUTS_UNSPECIFIED`, even when their source code also exists in NUTS 2024. This preserves historical evidence while preventing unsupported current-vintage claims. A later migration/audit may identify legacy local rows that were written under the former implicit-`NUTS_2024` rule; such rows must not be deleted or rewritten without an explicit evidence-based migration rule.

## G2 legacy-vintage audit path — 2026-10-10

Repository support now exists for the remaining private-local G2 check: run the read-only legacy NUTS audit against the persistent AUGUR DuckDB, preserve the JSON artifact, then decide any migration from exact evidence. Definite non-2024 codes can be identified without deleting history; rows whose codes also exist in NUTS 2024 remain vintage-unverified and must not be mass-relabelled merely from code equality.

## G2 local legacy reconciliation — evidence snapshot 2026-10-10

The user's read-only DuckDB audit found 199 legacy `NUTS_2024` observation groups, including **10 demonstrably invalid groups / 172 stored observations** on five retired NUTS2 codes (`IE01`, `IE02` in 1999–2011; `PT16`, `PT17`, `PT18` in 1999–2018), and **five invalid current registry rows** matching those codes. The remaining 189 observation groups have current code membership but **unverified boundary vintage**. No NUTS vintage may be inferred from code equality alone.

A copy-only reconciler is available, from `backend/` using the project venv:

```powershell
.\.venv\Scripts\python.exe -m scripts.reconcile_legacy_nuts_vintage --report "$HOME\Downloads\AUGUR_NUTS_VINTAGE_AUDIT_20261010.json"
```

This defaults to a **read-only dry run**, re-checks GISCO, matches the local audit snapshot and aborts on observation primary-key collisions. Optional `--output-db "$HOME\Downloads\augur_analytics_reconciled.duckdb"` makes a **new file**, relabels only the definitively invalid observation rows to `NUTS_UNSPECIFIED`, removes only corresponding invalid current-registry rows from **the copy**, and verifies total observation preservation in a transaction. Source database remains unchanged. Run while AUGUR's writer is stopped to obtain a consistent file snapshot. **Do not replace the active database automatically.** Validate the copy, examine application read behavior, preserve a backup, and perform operator-controlled adoption separately. Audit/CI alone does not close G2.
