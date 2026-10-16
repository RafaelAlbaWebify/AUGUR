# Geographic Rankings and Unified Comparison — Delivery Roadmap

Date: 2026-10-16. Status: **planned; no implementation or data acceptance claimed**.
Owner: AUGUR. Product intent: discover, rank, compare and eventually recommend locations using real evidence. This is the focused delivery plan under the existing [evidence-gated roadmap](ROADMAP.md), not a replacement for G3, C1, P1 or T1.

## Non-negotiable constraints

- Preserve the operator-accepted Country Radar layout (PR #47, 2026-10-16). No navigation or styling redesign of that view as part of ranking work.
- Reuse FastAPI, DuckDB, SQLite, React/TypeScript, the existing geographic catalog, ComparePanel and OverviewPage regional/city evidence paths.
- A registered geography is not a proven indicator observation. A green CI run is not local real-data acceptance.
- Comparability is enforced on the backend using indicator semantics, period, unit, geographic level/system and boundary vintage; ineligible results are excluded with reasons. No fabricated values, hidden fallback or falsely global claims.
- No modifications to the user's persistent DuckDB/SQLite or local worktree without safeguards. One permanent local checkout; use GitHub branches/CI, merge reviewed green routine PRs without repeated approval.
- Avoid arbitrary completion percentages. Status per workstream: planned, implemented, CI validated, real-evidence validated, operator accepted, or blocked.

## Milestone summary and dependency chain

| ID | Priority | Deliverable | Dependency | Status | Product acceptance evidence |
|---|---|---|---|---|---|
| GR-0 | P0 | Real evidence and existing API/code audit | None | Planned | Inventory for ESP/PRT/IRL with exact indicator×geo level×source×period×unit×vintage counts and blocked use cases; no DB write |
| GR-1 | P0 | Geographic identity, indicator catalog and comparability contract | GR-0 | Planned | Reviewed documented eligibility policy; tests cover valid, incompatible and ambiguous cases |
| GR-2 | P0 | Read-only ranking backend/API | GR-1 | Planned | Stable sorted outputs, deterministic ties, eligible denominator, exclusions, pagination and provenance; tests |
| GR-3 | P1 | Rankings page and discoverable navigation | GR-2 | Planned | Operator can filter, sort, inspect a source, share URL, and interpret missing/partial data |
| GR-4 | P1 | Unified 1–3 location Compare workflow | GR-1, GR-3 | Planned | Same/different countries supported for eligible cities, regions and countries; mixed-level context explicitly separated |
| GR-5 | P1 | Local real-data end-to-end acceptance | GR-3, GR-4, G3 evidence | Planned | Reproduce at least one cross-country country, one region and one city ranking (only if real comparable city data exists); otherwise explicit blocker |
| GR-6 | P2 | Personal decision ranking (housing + employment pilot) | GR-5, P1 evidence | Planned | Reproducible weighted outputs with feasibility, sensitivity and missingness; no arbitrary \"best city\" claim |
| GR-7 | P2 | Wider international coverage and release | GR-5 + verified source onboarding | Planned | New country/region/city datasets individually source-accepted, with explicit scope, never inferred global completeness |

## Work packets (batch changes into cohesive PRs)

### GR-0 — Evidence audit (first task)

1. Map live FastAPI endpoints, data models, geographic identifiers and Compare/Overview consumers; avoid building duplicates.
2. Produce a **read-only** exporter of actual DuckDB counts by indicator, geography, system/vintage, time and source, with missingness and canonical unit. Reuse existing G3 provenance export if suitable; don't duplicate tooling.
3. Validate what GitHub/source workflows can independently establish; identify precisely which facts require a sanitized local export and request only that minimum.
4. Produce an evidence-ready indicator shortlist: at least employment, unemployment, income and housing where actually available; mark city gaps rather than hiding them.

**Exit:** auditable inventory plus implementation mapping and prioritized eligible metrics. Do not claim ranking-ready until observations are evidenced.

### GR-1 — Shared contracts

- Stable location ID including country ISO3, geo code, level, source system and boundary vintage. Disambiguate homonyms and current/historical boundaries.
- Searchable metric catalog: ID, plain title, meaning, direction, units, supported levels, legitimate periods and coverage.
- Deterministic ranking eligibility: same indicator construct, compatible numerator/denominator and unit, stated reference period/window, compatible geographic definition; no city-versus-region mixed numerical ranking by default.
- Canonical sort: numeric value then stable geo ID; deterministic handling of ties, zero and negative values. Numeric direction means high/low, not good/bad.
- Explicit distinct states: no registered geos, no observations, incompatible data, partial valid coverage, stale periods, source error.

**Exit:** contracts and unit tests addressing boundary-vintage collisions, repeated observations, missingness, incompatible methods and ties.

### GR-2 — Ranking API (read-only)

Suggested new endpoint (verify routing conventions first): `GET /api/rankings?indicator_id=...&level=city|region|country&countries=...&period=...&sort=asc|desc&limit=...&cursor=...`.

Return filters, ranking population definition, total registered/eligible/observed/excluded counts, stable rank and ties, page metadata, per-row value/unit/period/source/geography and exclusion-reason aggregates. Never conflate catalog count with eligible observations. Pagination must be globally ranked, not independently sorted page by page. Cache key includes filter and evidence version. Explicit versioning for changing datasets.

**Exit:** backend/API tests; no changes to source measurements; queries performant on realistic local-sized fixtures.

### GR-3 — Rankings UX

- Add **Rankings** entry to existing navigation, without replacing Country Radar.
- Task-first defaults: search a metric, country/region/city level, coverage scope, period, lowest/highest; show ranked results immediately once eligible.
- Ranked table: position, location and country, value + unit, period, source/definition link; sorting and accessible status messages.
- Advanced filters collapsed initially. Clear banner: “X eligible locations from Y registered locations, covering [scope/years]”; no “worldwide best” when source scope is partial.
- Select up to three results; `Compare selected` handoff; links back to detail and shareable filter URLs.
- Keyboard, mobile and no-data/error states; no fake chart numbers in production.

**Exit:** CI frontend/build/browser, operator screenshots at representative widths and local source-backed acceptance.

### GR-4 — Unified Compare

- Replace fixed-country-only slots with up to three independent location selectors, keeping existing country comparison features intact.
- Permit same- or cross-country comparable city/city and region/region comparisons, including different countries; constrain by metric semantics and geography methodology rather than arbitrary national borders.
- Display cross-level (city/region/country) values as **context** unless an explicitly valid comparison contract exists; do not numerically rank incompatible levels.
- Preserve metric, period and provenance through Rankings ⇄ Compare and support a one-location detail state.
- Evidence explanations, change-over-time when matched series exist, explicit missing cells.

**Exit:** browser tests for 1/2/3 selections, cross-country, same-country, mixed levels, no overlap and incomplete data, plus operator validation.

### GR-5 — Real-data acceptance gate

- Test with actual stored evidence and authoritative source/period/vintage references; reconstruct at least one ranking from read-only SQL independently of API/UI.
- Assess country, region and city separately; if comparable city observations are insufficient, report a **blocked city ranking** and start a targeted ingestion work packet, not simulated production output.
- Validate copy/export provenance; verify no regression in current Country Radar and national Compare.
- Record operator acceptance of responsiveness, comprehensibility, and scope labeling.

### GR-6 — Personalized decision extension (not a prerequisite for basic ranking)

Start narrowly with housing purchase affordability and profession-relevant employment, only once defensible local earnings/occupation/housing evidence exists. Require editable priorities, hard constraints (e.g. legal feasibility/budget), transparent units and scoring, missing data handling, rank sensitivity, and explanations. Use existing Personal Fit/FinancialFit where appropriate. Never equate a basic single-indicator ranking with a personally optimal decision.

### GR-7 — World expansion

Onboard source-by-source and geography-by-geography under the [global expansion contract](GLOBAL_EXPANSION_CONTRACT.md), with observed counts and comparability tests. “Worldwide” means a scope filter, not a completeness guarantee. Do not promise unrestricted city coverage without auditable evidence.

## Baseline UX contract

1. User asks “Where is [metric] highest/lowest?” and selects a geographic level.
2. Ranking appears with meaningful coverage, source, period and exclusions.
3. User selects up to three places; Compare opens with selections and metric preserved.
4. User can inspect full location evidence and return with filters intact.
5. A city absent from an index is distinguished from a city with no evidence; unavailable ranking is honest, not empty-looking success.

## Regression and delivery discipline

- Golden browser regression for 1650×900 Country Radar: Country | Map | Changes and metrics below; no layout regression.
- Backend tests for source semantics, vintages, period alignment, unit equivalence, duplicates, stable rank and pagination.
- API integration tests and Playwright for filter URL, location selection, handoff, accessibility and missing states.
- Preserve original local DB files and no extra permanent worktrees.
- Per milestone publish: PR, commit, CI evidence, real-data evidence, remaining blockers and next action. Update PROJECT_STATE/ROADMAP/HANDOVER as needed.

## Immediate next action

Execute **GR-0** as a single coherent audit PR: code-path map + read-only coverage matrix + acceptance blockers + first eligible indicator shortlist. Evaluate existing G3 exporters first; do not require user to run diagnostics that can be executed or tested on GitHub. After audit, use results to narrow GR-1/GR-2 implementation and determine whether a sanitized local export is essential.
