# AUGUR 10 — Persistent remediation and detailed-review register

Updated: 2026-10-17. Basis: main HEAD bab3d35c (PR #114), open PR #115 at review time. This is a **triage and remediation planning record**, not a claim that fixes have been implemented or tests passed.

## Canonical evidence and accounting
- `docs/audit/inventory.json`: 351 eligible files; 313 Python files; 1,624 AST definitions; 57 SHA-verified reviewed; 0 stale at observed snapshot; **16.24%** review.
- `docs/audit/findings.json`: canonical machine-readable register (77 findings at observed snapshot). Keep IDs, severity, file SHA, remediation, and state there; do not overwrite or duplicate those entries.
- `docs/audit/README.md`: review methodology and batches. Code review, source-data acceptance, CI and operator acceptance are separate gates.
- New detailed review below is **not counted** as SHA-verified line-by-line coverage until its exact source SHA, entire file ranges, dependent consumers and tests have been added to findings.json and regenerated inventory agrees.
- Source data and local operator databases are not to be modified without explicit authorization and backup/restore rehearsal.

## Immediate B03 review outcomes and work queue

| ID | Status | Priority | Source and observed reason | Proposed change | Required acceptance |
| --- | --- | --- | --- | --- | --- |
| AUG10-01 | Open; confirmed source behaviour | High | `backend/app/services/peer_reference.py`, main fetched blob 098860eb: builds per-period floats and numeric ranks across countries without checking units, provider/dataset, flags or same-observation semantics; existing AUD-B03-019 covers primary risk. | Add explicit source comparability contract, filter or reject conflicting observation tuples and expose exclusions/provenance; never present unmatched rows as comparable. | Mixed-unit, mixed-vintage, mixed-dataset and flagged-observation fixtures; service/API assertions; no unauthorized rankings. |
| AUG10-02 | Investigate, not certified defect | Medium | `peer_reference.py` period mapping `{int(row['period']): row for row in rows}` silently overwrites duplicates for a year; `float(value)` accepts nonfinite values and can throw for malformed observations. | Define duplicate and malformed-value policy (fail closed, explicit reason); validate period format and finiteness before rank. | Duplicate conflicting provider rows, `NaN`, `Infinity`, string/null values, unstable input ordering; assert deterministic blocked/partial response. |
| AUG10-03 | Open; existing AUD-B03-014 | High for misleading fit | `financial_fit.py` verifies positive finite income/price numbers after PR #110, but combines most recent origin and target price-level indices irrespective of matched period. Return includes only target `source_id`, not provenance for both sides. | Require compatible period, provider, unit, coverage and currency basis; include bilateral source details; do not claim comparable income when any check fails. | Cross-vintage, cross-provider, non-euro income, invalid and missing cases. Distinguish numeric guard (already implemented) from comparability gate (open). |
| AUG10-04 | PR pending; do not count fixed | Medium | PR #115 changes `backend/app/services/scenarios.py` from `horizons or DEFAULT_HORIZONS` to explicit `None` fallback. On main, explicit `[]` incorrectly falls back to defaults. | Verify PR #115 tests, mergeability and CI, then merge only when green; review consistency with `trajectory.py` AUD-B03-012. | Explicit empty, missing, normal list and malformed horizons throughout API/service/DB. |
| AUG10-05 | Open; AUD-B03-017 | Medium | `esco_match.py` substring matching can equate Java with JavaScript and inflate claimed essential skills. | Use exact-normalized tokens or ESCO concept-based matches with explanation; retain unverified semantic matches as candidates. | False-positive and true-positive fixtures plus career fit consumer behaviour. |
| AUG10-06 | Open; AUD-B03-018 | Medium | `live_postings.py` posting counts may coerce booleans/fractions/strings and lack provider-origin proof. | Strict integer nonnegative validation and provenance trust contract. | Count edge cases and provider identity tests; no unjustified job-market confidence. |
| AUG10-07 | Open; AUD-B03-008/007 | Critical release gate | Regional ranking vintage currently accepts caller-supplied `verified_geo_ids`; independent NUTS vintage and Eurostat `d/u` flag policy remain unapproved. | Derive verification solely from independently certified source-bound registry; enforce dataset-specific flag rules; keep numeric rankings blocked. | Request-tampering test, exact boundary/vintage proof, official quality policy, real read-only reconciliation. |
| AUG10-08 | Open; AUD-B03-011 | Medium | Compare service can group same indicator with mismatched units and periods. | Reuse same comparability contract as AUG10-01, avoid parallel inconsistent policies. | Mixed-source and mixed-year full country comparison fixtures. |
| AUG10-09 | Open; AUD-B03-006 | High operational safety | API startup bootstraps DB and may mutate data on nominal read-only launch. | Separate initialization/migration from read-only serving; explicit permission and preflight. | Snapshot DB bytes before/after read-only startup and migration dry-run. |
| AUG10-10 | Open; AUD-B03-010/013 | Medium | EEA GISCO global cache can be stale; persisted country metadata may be overlaid with stale catalog entries. | Cache version/source-key and invalidation; explicit authoritative precedence. | Injected-client/version changes and persisted newer metadata tests. |
| AUG10-11 | Open; AUD-B03-015/016 | Medium | Legal and language heuristics risk interpretation as legal or job eligibility. | Explicitly contextual status and consumer labels; provider/jurisdiction validation before any eligibility claim. | Multiple languages, occupation-specific requirements, API/UI copy regression. |
| AUG10-12 | Pending inventory enhancement | Medium | JS/TS/PowerShell source files have path/hash inventory but lack semantic symbol and reverse-call mapping. | Add language-specific parser passes with explicit coverage and limitations, preserving canonical inventory. | Deterministic fixtures and SHA invalidation, including PowerShell commands/workflows and TypeScript imports. |

## Existing B02 and data-quality blockers that must remain open
- Official provider-specific IMF/WEO actual-versus-forecast metadata and missing series/country coverage.
- Eurostat exact dimensions, status flags and NUTS geography vintage; 31 historical operator employment observations were stored using wrong age cohort, with only isolated correction rehearsal authorized.
- DB ingestion atomicity, geography metadata preservation and rollback risks tracked in AUD-B02 records.
- CI or code completion cannot alone accept real provider data or historical production migration.

## Next disciplined implementation sequence
1. Check PR #115's full tests/status and harmonize `scenarios.py`/`trajectory.py` empty-horizon behaviour, avoiding overlapping branches.
2. Complete peer/compare/financial source comparability contract as one cohesive design; read analytics SQL and API/frontend consumers before coding.
3. Build strict negative-path unit/integration fixtures and fail-closed response states before enabling new numeric output.
4. Continue B03 source-by-source SHA review; write new machine entries in `findings.json`, regenerate inventory and report actual numerator/denominator.
5. Follow with B04–B06 and JS/TS/PowerShell semantic inventory. No false release percent.

## Definition of resolved
A finding is only resolved after verified source fix, relevant tests, green CI, merge on main, updated SHA evidence and (where needed) separate real-data/operator acceptance. This file contains **proposed fixes only**; no application code has been altered in this AUGUR 10 checkpoint.
