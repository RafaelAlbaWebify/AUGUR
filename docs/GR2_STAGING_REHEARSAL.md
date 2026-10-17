# GR-2 staging rehearsal — production untouched

The 2026-10-16 operator audit found **31/31 stored 2025 regional employment rates numerically identical to Eurostat Y15–64** and none matching the indicator's Y20–64 cohort. The ingestion's normalizer and category selection have been fixed, but original request/response metadata was not retained. An exact numerical match does not reconstruct historical source provenance.

## Isolated staging tool

```powershell
Set-Location "$HOME\Documents\GitHub\AUGUR\backend"
.\.venv\Scripts\python.exe -m scripts.stage_gr2_employment --output "$HOME\Downloads\AUGUR_GR2_EMPLOYMENT_STAGE.duckdb" --report "$HOME\Downloads\AUGUR_GR2_EMPLOYMENT_STAGE_REPORT.json"
```

**Close AUGUR before running.** The script refuses to copy the analytical DuckDB if its WAL file exists and verifies original SHA-256 before and after source retrieval/copy/staging. It also refuses to overwrite an existing staging destination.

Source EUR0STAT data is fetched with exact annual 2025 Y20–64, both-sex percent dimensions for each locally registered ESP/PRT/IRL region. All expected geographies must be present, each with one exact-cohort observation. The script copies the original DuckDB to a **new isolated file**, preserves a `gr2_remediation_before` table there, updates **only the staged copy**, records values, metadata and quality flags, and produces a JSON difference report. On failure, it removes only its own incomplete newly created staging copy. The source database is never opened in write mode.

This is an **isolated rehearsal, not a verified backup/restore procedure**. A separately managed backup and tested recovery are still required before any approved production change. The staged copy is not automatically promoted. The script does not modify source data even if every staged value matches the API.

## Source quality and geographic-vintage blockers

Eurostat documents observation status `d` as **definition differs (see metadata)** and `u` as **low reliability** (Eurostat's [flag hierarchy](https://eurostat.github.io/flagr/articles/flagr_introduction.html) and [glossary](https://ec.europa.eu/eurostat/web/user-guides/data-browser/introduction-navigation-data/glossary)). Both remain blocked from certified rankings until dataset-specific methodology review. Do not silently drop the flag or force a row eligible.

Eurostat documents [NUTS 2024](https://ec.europa.eu/eurostat/web/nuts) as in force since 1 January 2024. That establishes the classification's existence but does not, alone, establish the boundary vintage used by a particular historical observation. The ranking API must continue rejecting unverified vintage.

## Following gates

- Verify staging file and independent source evidence without modifying original.
- Identify Eurostat's dataset-specific explanation for `d` in Spanish regional LFS.
- Resolve unemployment 2025 local-versus-provider discrepancies separately.
- Validate restored offline backup and rehearse rollback.
- Independent source/vintage proof, approval and exact SQL-to-API rank-order equivalence.
- Operator browser acceptance of the GR-3 blocked and successful evidence states.
