# GR-2 historical numerical evidence — bounded read-only sample

Run from the existing backend directory:

```powershell
.\.venv\Scripts\python.exe -m scripts.inspect_ranking_historical_sample --output "$HOME\Downloads\AUGUR_GR2_HISTORICAL_SAMPLE.json"
```

This samples **ES11, ES30, IE04, PT11, PT20, PT30** for both 2025 regional employment and unemployment. The source is queried with exact requested Eurostat dimensions, including `isced11=TOTAL` for unemployment. The local DuckDB is opened read-only. If its provenance columns predate GR-2, nulls are recorded rather than inferred.

The output includes **actual local and provider rates**, the signed difference in percentage points, returned dimensions and quality flag. These are public aggregate statistics, not personal records; nevertheless inspect the JSON before sharing. Reports cannot independently certify historic local observations' NUTS boundary vintage or explain historical ingest behavior from absent provenance. If ambiguity or source failure occurs, report the issue and do not guess.

This is a diagnosis, not a remediation or database migration. Do **not** overwrite values or relax ranking gating based solely on this sample.
