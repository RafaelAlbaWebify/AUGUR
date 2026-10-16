# GR-2 employment cohort forensic sample — 2026-10-16

The operator's six-region GR-2 historical sample established that all local 2025 regional employment rates were 5.1–5.8 percentage points **below** the fresh age-20–64 Eurostat values. Local request/response provenance is null. That pattern is consistent with, but does **not** prove, the possibility that local values refer to a different age cohort.

Run the bounded **read-only** comparison from `backend`:

```powershell
.\.venv\Scripts\python.exe -m scripts.inspect_ranking_employment_age --output "$HOME\Downloads\AUGUR_GR2_EMPLOYMENT_AGE_FORENSICS.json"
```

It compares the six codes ES11, ES30, IE04, PT11, PT20 and PT30 against `lfst_r_lfe2emprt` for 2025, both sexes, percent, separately requesting **Y15-64** and **Y20-64**. Each returned observation is normalized against explicit request dimensions. It reports actual aggregate source and local values, signed differences, matching within 0.051 percentage points and quality flags, with DuckDB opened read-only.

Even an exact Y15–64 match does **not** retrospectively prove which request selected the historical local value. Missing source cohorts and fetch failures remain unresolved, rather than assumed absent. Do not overwrite persistent observations, infer vintage, or bypass the ranking eligibility gate from this diagnostic alone.
