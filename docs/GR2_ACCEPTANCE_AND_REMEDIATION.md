# GR-2 acceptance and controlled remediation

## Operator command

From the existing AUGUR repository:

```powershell
.\tools\acceptance.ps1 -Scope GR2 -Mode ReadOnly
```

This runs `backend/scripts/accept_gr2.py`, reports DuckDB SHA-256 and row/provenance inventory, 2025 employment and unemployment source reconciliation, and full registered 2025 employment Y15–64 versus intended Y20–64 comparison. It creates a single JSON file in Downloads. It never executes DuckDB writes. A real-data run requires Eurostat network access; provider failures are explicit, not silently classified as matches. The returned `database_unchanged` flag verifies the same database hash and size before and after. If another process writes concurrently, the reported fingerprint may change, which is flagged rather than hidden.

## Confirmed operator findings as of 2026-10-16

31/31 stored NUTS2 employment figures for 2025 match Eurostat's Y15–64 observations exactly (19 ESP, 9 PRT, 3 IRL); zero match intended Y20–64. Historical request and response dimensions are not stored. Unemployment V4 found only 1/31 within 0.051 percentage points, 29 value discrepancies, and one quality-review flag. Existing DuckDB contains unaccepted values; a live source re-fetch cannot retrospectively certify the historical geography vintage.

## Staging and recovery gates (not yet executed)

1. Define immutable snapshot of current analytical DuckDB plus app SQLite where relevant, including sha256, sizes, transaction-consistent state and secure backup location.
2. Verify **restore into an isolated location** and use DuckDB read-only `SELECT`/integrity checks against the restored copy. A filename or checksum alone does not prove restoration.
3. Build proposed replacement values only from exact Eurostat 2025 `freq=A, age=Y20-64, sex=T, unit=PC`, plus `isced11=TOTAL` for unemployment; retain provider tuple, status flag, source timestamp and observation provenance. Do not overwrite historical rows in-place during diagnostics.
4. Produce a dry-run difference report and independent expected ranking SQL with count, uniqueness, sorted order and quality gate decisions; reject missing, duplicate or invalid source responses.
5. Independently establish observation-specific GISCO/Eurostat boundary vintage. A `NUTS_2024` code label alone does **not** prove the observation's boundary system.
6. Obtain a documented and reviewed Eurostat quality-flag policy, especially `d` and `u`. Pending that policy, flagged rows are excluded from certified numerical ranking.
7. Request explicit operator approval before any production mutation. Implement an atomic, audited transaction with rollback only after a restored-copy rehearsal. Preserve original observational evidence.

## Ranking UI acceptance scope

GR-3 can show indicator and country filters and meaningful blocked/no-observation states immediately. Until all evidence gates pass, it must not expose incorrect numeric leaderboards or claim a verified ranking. Preserve operator-accepted Country Radar layout.

## Pending

- Exact authoritative observation-to-boundary vintage proof.
- Official-source interpretation and eligibility policy for quality flags.
- Real local read-only acceptance report from the new combined runner.
- Staged database remediation and tested recovery; no production writes approved.
- Ranking API to UI end-to-end acceptance with certified data.
