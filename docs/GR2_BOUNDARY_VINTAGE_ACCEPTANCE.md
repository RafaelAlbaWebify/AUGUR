# GR-2 boundary vintage acceptance — pilot labour rankings

Date: 2026-10-16. State: **source documentation verified; per-observation boundary proof pending**.

## Official source basis

- [Eurostat NUTS history](https://ec.europa.eu/eurostat/en/web/nuts/history): NUTS 2024 applies to data transmission from 2024 through 2026; code membership and reference year are distinct facts. Historical time series may be recoded, but not always.
- [Eurostat regional yearbook 2025](https://ec.europa.eu/eurostat/documents/15234730/22226461/KS-01-25-037-EN-N.pdf/d1e913e6-7903-cabc-4171-73cb06225f1a): NUTS 2024 forms the regional statistical classification, with historical recoding limitations.
- [Eurostat regional labour market metadata](https://ec.europa.eu/eurostat/cache/metadata/en/reg_lmk_esms.htm): NUTS2 LFS data show broadly comparable geographic reporting, subject to indicator dimensions, revisions, flags and temporal consistency.

These statements make 2025 NUTS2 labour a **credible** pilot; they do not establish the exact vintage of each AUGUR stored observation or that all entries were ingested with compatible dimensions.

## Evidence procedure

1. Confirm official NUTS 2024 codes for each candidate from the authoritative GISCO registry (as in existing G2 workflow), rather than assume from stored `geography_system`.
2. Run the read-only exporter `backend/scripts/export_ranking_vintage_audit.py` for both pilot indicators. This yields exact local geo code, source/dataset/year/unit identities and row counts **without numerical values**.
3. Cross-check dataset-specific Eurostat response dimensions and flags for the reported code/year/indicator set, including age band, sex, rate denominator and selected statistical unit.
4. Record whether observations can be assigned a verified reference boundary vintage, with an explicit evidence reference. Do not propagate `boundary_verified=True` from code or period matching alone.
5. When successful, implement a trustworthy verification adapter with explicit evidence provenance, then enable those rows in `/api/rankings/regions`; require independently reproducible ordering from local DuckDB.
6. If proof remains unavailable, leave the endpoint in `blocked_unverified_evidence` and show precise causes and next validation action.

## Local minimal evidence command

From the single AUGUR repository after pulling merged code:

```powershell
Set-Location "$HOME\Documents\GitHub\AUGUR\backend"
.\.venv\Scripts\python.exe -m scripts.export_ranking_vintage_audit --indicator regional_unemployment_rate --output "$HOME\Downloads\AUGUR_GR2_UNEMPLOYMENT_VINTAGE.json"
.\.venv\Scripts\python.exe -m scripts.export_ranking_vintage_audit --indicator regional_employment_rate --output "$HOME\Downloads\AUGUR_GR2_EMPLOYMENT_VINTAGE.json"
```

The source database is opened read-only and neither private values nor backups are exported. Outputs are local artifacts only. Results must be examined against official provider semantics before a certified ranking is displayed.
