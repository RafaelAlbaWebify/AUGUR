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
