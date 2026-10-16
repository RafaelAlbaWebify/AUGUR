# GR-2 live official-source replay (read only)

The stored 2025 ESP/PRT/IRL NUTS2 labour pilots can now be **compared numerically to live Eurostat dataset responses without altering the local DuckDB**. This is an acceptance aid, not automatic certification.

Run from the existing `backend` directory after updating `main`:

```powershell
.\.venv\Scripts\python.exe -m scripts.reconcile_ranking_eurostat --output "$HOME\Downloads\AUGUR_GR2_LIVE_SOURCE_RECONCILIATION.json"
```

The exporter queries `lfst_r_lfu3rt` and `lfst_r_lfe2emprt` with existing annual, Y20-64, sex-total, percentage filters, year 2025, and only the registered local pilot geographic codes (grouped by country). It compares stored values with fresh provider values to a disclosed 0.051 percentage-point tolerance and checks the **actual response** geo, period, age, sex, frequency, unit, and quality-status flag. It reports code-level issue reasons and match counts, not individual numeric values or local DB modifications. Network and Eurostat availability are necessary. Any request failure is recorded as an unresolved issue, not as verified data.

**Still required before accepting numerical rankings:** official reference-boundary-vintage evidence for provider observation cohorts, authoritative interpretations of quality flags, source response consistency, and locally reproducible ranking order. A fresh value match alone does not prove historical boundary equivalence. No production eligibility override is introduced.
