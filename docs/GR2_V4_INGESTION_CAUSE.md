# GR-2 V4 — confirmed ingestion ambiguity and safety correction

Operator's read-only replay of 2025 NUTS2 cohorts (ESP19, PRT9, IRL3 per metric) yields:

- Unemployment: **1/31** within 0.051 percentage points; **29** value discrepancies (usually 0.1–0.5 percentage points), **1** source quality-flag review; zero duplicate-provider-row reports after `isced11=TOTAL`.
- Employment: **0/31** within tolerance, with 31 differences ranging **4.5–7.6 percentage points**. These are not plausibly rounding differences.
- This is **not evidence that the source's current values are wrong**; the historical local ingestion's original dimension selections were not preserved.

## Confirmed code-path defect

`_latest_regional_indicator` passed `indicator_id`, `dataset_id` and display `unit` to `EurostatAdapter.normalize`, **but omitted `dimension_values`**. Consequently, normalizer could return several categories for the same geography/year while the selector used `max(rows, key=lambda row: row["period"])`. In a year with multiple category slices, this silently selected the first arbitrary row, without validating age, sex, education or other dimensions. This is a genuine ingestion integrity defect irrespective of the final root cause of every numerical mismatch.

## Fix scope

The regional ingestion code now passes all exact requested source filters as `dimension_values` into normalization and rejects multiple surviving rows for the same year. New regression tests cover both behaviors. No existing DuckDB values are changed and existing rankings stay blocked.

## Safe next steps

Use a **read-only locally produced numerical pairing for a few representative codes**, including the original row's stored request and response metadata if any, to distinguish stale values from prior arbitrary category selection. Do not alter the existing DB on the basis of the current reconciliation or force `boundary_verified=True`. A protected refresh/rebuild strategy should be designed only after the historical contamination is measured, and statistical vintage separately verified.
