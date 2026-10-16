# GR-2 replay correction — observed local findings (2026-10-16)

Operator-provided `AUGUR_GR2_LIVE_SOURCE_RECONCILIATION.json` reports 31 local and 31 provider-returned geographies for **each** 2025 labour cohort, but zero certified matches. This report is a diagnostic, not evidence that all 62 local values are incorrect.

- Unemployment (`lfst_r_lfu3rt`): 29 `multiple_provider_rows`, 2 `provider_dimensions_or_status_review_required`.
- Employment (`lfst_r_lfe2emprt`): 19 `provider_dimensions_or_status_review_required`, 12 `value_discrepancy`.
- Original source replay counted any two provider rows for the same geography as duplicates **before checking their actual dimensions**. This is incorrect for multi-slice JSON-stat responses; a different age, sex, frequency or unit is not a duplicate of the accepted cohort.
- Corrected replay selects **exact response** annual/Y20-64/T/PC/2025/geo tuples before duplicate detection and value comparison. A flagged exact cohort remains review-required. No local numeric values are exported, and DuckDB remains read-only.
- Original 12 employment discrepancies still need independent re-evaluation; no values are overwritten and no rankings are unlocked by this correction.

After merging, rerun `python -m scripts.reconcile_ranking_eurostat --output "$HOME\\Downloads\\AUGUR_GR2_LIVE_SOURCE_RECONCILIATION_V2.json"` from `backend`, upload the resulting report, and distinguish value discrepancies from quality flags or unresolved provider dimension slices. Boundary vintage and observed-value quality acceptance remain separate gates.
