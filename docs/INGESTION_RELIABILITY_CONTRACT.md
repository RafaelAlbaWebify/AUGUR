# Ingestion reliability contract — implementation programme

Status: first fail-closed Eurostat parser hardening in progress. This is **not** universal source certification.

## Problem demonstrated by genuine local evidence
2025 NUTS2 employment stored for ESP/IRL/PRT used Y15-64 while the configured ranking indicator intended Y20-64. Historical response dimensions were not preserved. Stage-only corrected 31 observations; 19 Spanish rows carry Eurostat status `d`, and no boundary-vintage certification exists. Production is unchanged.

## Required source-to-product invariants
1. Declare a reviewed **dataset-specific source contract** before writes: provider, dataset, response dimension codes (including age/sex/education/frequency), measure, output units, geographic system, allowed period and observed/forecast distinction.
2. Inspect **actual returned dimensions**, not merely requested HTTP filters. Preserve request and response metadata and status flags with each observation. Refuse missing, duplicate or contradictory tuples; do not select arbitrary first rows.
3. Validate finite numeric values, JSON-stat coordinate cardinality and schema. Zero is valid; missing is not zero. Do not mutate persistent stores if a validation gate fails.
4. Verify geography identifiers against source-appropriate authoritative current registries. Keep **source boundary-vintage unknown** separate from official current registry membership.
5. Apply source-specific quality-flag policy. Unknown or flagged rows remain traceable but must not be asserted fully comparable until methodologically accepted.
6. Perform complete-batch validation (expected territory and indicator coverage, duplicate keys, periods, definitions) **before transaction**. Record rejected rows and reasons, never synthesize observations.
7. Use staged write / atomic promotion with checksum, before image, verified backup and restore rehearsal; production migration requires explicit operator authorization.
8. Run provider contract fixtures and adversarial tests in CI; scheduled real-source smoke tests must exercise the same normalizer/write guards. No green-CI-to-real-data conflation.
9. API and UI report denominator, provenance, units, period, quality and missingness. Rankings remain blocked if comparability/vintage not accepted.

## Audit scope and rollout gates
- **Gate A:** enumerate every production ingest entrypoint, adapter, normalizer and datastore write; build a matrix marking which invariants are already enforced, missing or intentionally source-exempt.
- **Gate B:** define shared validation primitives (finite values, dimension tuples, duplicate keys, provenance) and install them on every Eurostat and OECD write path; preserve provider-specific semantics.
- **Gate C:** transactional batch validation and source-live acceptance for employment/unemployment, followed by pilot indicator families.
- **Gate D:** controlled persistent-store reconciliation and independent source/SQL/API equivalence.
- **Gate E:** nightly regression/source-change watch, operator signoff and gradual ranking unlock.

## Initial patch scope
Eurostat `normalize` now refuses malformed dimension layout and nonfinite/non-numeric actual observations. Tests cover zero, NaN, infinities, booleans, text, invalid dimension size and duplicate dimension identifiers. **This patch does not alter historical rows, enforce cross-provider contracts, or authorize rankings.**

Next implementation should audit alternate normalizers (`normalize_earnings` and regional ingestion modules), generic `upsert_observations` / `upsert_subnational_observations`, OECD adapters, and all scripts that bypass common validation. A single automatic acceptance runner should report the results; do not require the user to repeat manual source audits.

## 2026-10-17 observation-write transaction gate

Source-to-database review found national and subnational generic upserts opening DuckDB before checking all rows, and subnational writes doing geography registry and observation replacements without an explicit transaction. This package adds a batch-level finite-value, identity, period and duplicate-key guard, plus explicit rollback on failure for those two entrypoints. This is *not* universal ingestion certification: alternate specialized write paths (OECD, ESCO, earnings etc.) still require independent inventory and source-specific dimension policy. Historical local DuckDB remains unchanged. A merged CI pass establishes code correctness, not NUTS vintage, source comparability or local recovery.

Acceptance: invalid later rows rejected before opening DB; duplicate keys rejected; valid national/regional fixtures accepted; complete backend/frontend/ops CI; tests of atomic rollback are next independent integration gate.

## 2026-10-17 database-to-HTTP acceptance batch

Disposable DuckDB integration tests cover three independent failure modes: malformed *later* input rejects the entire batch before write; a SQL constraint failure after geography-registry replacement rolls back both geography and observation changes; an explicit verified fixture reproduces the stored SQL observation in the ranking service while the actual public HTTP route blocks a vintage-unverified observation. No test opens the operator's production file.

The combined `sync_eurostat` regional path now validates exact labour and housing contracts plus duplicate/finite batch properties for labour, housing and health **before** executing a single regional observations upsert. Sector evidence still uses a specialized persistence routine and is outside this transaction. Country syncs still write separately and are not represented as an all-provider atomic import. Existing historical mislabelled cohorts, source flag policy, NUTS vintage and operator approval remain unresolved: no automatic release of rankings.

Acceptance gate: full CI, migration-free isolated fixture regression, and checked merge. Broader specialized write paths and safe production reconciliation need separate validation; keep blocked states explicit.

## Write-path inventory update — 2026-10-17
- Generic `observations` and `subnational_observations`: batch identity/finite-value prevalidation, explicit DuckDB transaction (PR #75, merged).
- Labour earnings, net earnings, job vacancy, OJA imbalance, shortage index, occupation outlook, job transitions, environmental health burden: dataset-key and field-specific numeric validation plus explicit transaction in PR #76; employment and forecast values may be nullable only where existing schema permits.
- `regional_sector_employment`: composite-key/numeric guard and own atomic transaction in PR #76. **Not** in the same transaction as labour/housing/health upsert.
- `sync_eurostat.py`: verify labour/housing contract and combined regional batch before a single generic observation upsert; earlier country syncs are not globally atomic.
- Other geography/catalog maintenance writers and per-provider semantic/quality/vintage decisions remain excluded from universal certification and must be audited independently. Test assertions and green CI are not authorization to modify local production.
