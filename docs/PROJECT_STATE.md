# AUGUR — Project State

Updated: 2026-10-09. **Canonical coordination entry point**, not a replacement for architectural or methodological specifications.

## Product purpose
Local-first country/region trajectory, employment intelligence, and personal fit. Separate *observations*, *official forecasts*, *candidate scenarios* and *personal fit*. Never invent or impute source observations to make a feature appear complete.

## Confirmed repository facts
- Backend: FastAPI, DuckDB analytics, SQLite application state; frontend: React/TypeScript; automated pytest/build/Playwright in GitHub Actions. See [ARCHITECTURE.md](ARCHITECTURE.md).
- National analysis, regional/city evidence, and TTV infrastructure exist in code; existence and green CI **do not establish** complete end-to-end operability.
- TTV full release is blocked by prospective external holdout calibration under the frozen protocol. See [AUGUR_REMAINING_IMPLEMENTATION_2026-10-07.md](AUGUR_REMAINING_IMPLEMENTATION_2026-10-07.md) and [TTV_VALIDATION.md](TTV_VALIDATION.md).
- Geographic coverage endpoint and local JSON/CSV exporter merged via PR #1; per-geo provenance exporter via PR #2; standalone official GISCO NUTS 2024 workflow via PR #3.
- Real local coverage export supplied on 2026-10-09: **26 country/system/level/indicator rows across ESP, IRL, PRT**. This is a local evidence inventory, not official provider universe coverage. OECD geographic systems were absent from that export; do not infer absence from OECD itself.
- Official GISCO 2024 catalog workflow completed and uploaded a source-grounded artifact in run [37924620862](https://github.com/RafaelAlbaWebify/AUGUR/actions/runs/37924620862). Log counts: ES NUTS2=19/NUTS3=59; IE=3/8; PT=9/26. These are catalog identities, **not observations**.
- PR #7 regional observation provenance inventory **merged** as `aa10370c` (CI green). No user local G3 export has been evaluated; acceptance remains pending.
- PR #4 exact-code local-vs-official comparison **merged** in `ff3766e8` after extending validation for malformed official catalogs and duplicate local codes. End-to-end comparison with the user's private geography provenance export remains unverified.

## Known discrepancies requiring investigation
- IRL NUTS2 local count 5 versus official 2024 catalog count 3; PRT NUTS2 12 versus 9. Could reflect historic/new boundaries, not automatically duplicates.
- ESP NUTS3 safety registered group 3 versus official 2024 NUTS3 catalog count 59: incomplete local registration for that group, not proof the published safety dataset lacks regions.
- IRL city population latest observations in the supplied file are 2011/2016. Historical coverage must not be labeled current.
- OECD non-EU regional and FUA ingest paths exist and by design differ from Eurostat/NUTS; they are not verified as globally complete in user's local store.
- User's DuckDB resides only on their PC; GitHub cannot inspect its contents unless a sanitized export is provided. Avoid repeating manual requests when GitHub can independently verify a prerequisite.

## Readiness: do not report a percentage yet
The earlier **42%** is an unsupported historical estimate, **retired** from progress reporting. Track each deliverable as *implemented*, *CI validated*, *real-evidence validated*, *product accepted*, or *externally blocked*. An overall percentage can be introduced only with an approved weighted denominator, baseline and acceptance record.

## Start here
1. Read [ROADMAP.md](ROADMAP.md), [VALIDATION.md](VALIDATION.md), [DECISIONS.md](DECISIONS.md), [HANDOVER.md](HANDOVER.md).
2. Check GitHub HEAD, all open PRs, runs, and current local-evidence blockers.
3. Advance the **highest-priority actionable milestone**, preferably in a coherent batch, with tests and actual evidence where available.
4. Update these coordination files in the **same PR** as consequential work. Never confuse green CI with production acceptance.

## Source of truth
Code/tests/workflows = implementation truth; [METHODOLOGY.md](METHODOLOGY.md) = methodological contract; source inventories = provider evidence; this file = current coordination snapshot. If there is a conflict, verify and record it in [DECISIONS.md](DECISIONS.md), do not silently overwrite.

## G3 source audit evidence — 2026-10-09

Real local ES/IE/PT coverage export was contrasted with configured Eurostat datasets and official dataset descriptions. See [G3 source audit](G3_REAL_SOURCE_AUDIT_2026-10-09.md). Confirmed important qualification: 3/3 ESP NUTS3 registered crime regions is not nationwide coverage; IRL/PRT NUTS2 historical-vintage mixing is suspected but exact codes remain unverified. The comparison establishes source contracts and observation-period discrepancies, **not a completed per-code reconciliation or repair**.

## Master indicator inventory (2026-10-10)

[Master indicator matrix](MASTER_INDICATOR_MATRIX.md) maps economic development, fiscal burden, housing, migration, institutional quality, freedom and living conditions across country/region/city scales. A deterministic generator `backend/scripts/export_indicator_inventory.py` inventories national indicator declarations but does **not** prove source coverage. Product priority shifts to completing P0 fiscal feasibility and actual housing affordability with authoritative source contracts and real observation acceptance. Existing G2/G3 local evidence gaps remain open; no invented readiness percentage.
