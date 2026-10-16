# GR-2 V3 reconciliation finding — 2026-10-16

The user-local V3 source replay reports **zero accepted matches out of 62**. The unemployment dataset returned 3–4 records per geography matching the existing core filters for 29 regions. The additional source dimension in every ambiguous case is **`isced11`**, the ISCED 2011 educational-attainment category. The [official Eurostat `lfst_r_lfu3rt` data browser](https://ec.europa.eu/eurostat/databrowser/view/LFST_R_LFU3RT__custom_6259067/default/table?lang=en) explicitly specifies `isced11=TOTAL` for the all-education unemployment rate.

The repository now adds `isced11=TOTAL` to the unemployment source request and checks the provider-returned education code in ranking and replay validation. The employment dataset `lfst_r_lfe2emprt` is a separate series without this ISCED dimension and is unaffected.

**Unresolved and not explained away:** unemployment PT20 delta 0.3 percentage points, PT30 delta 0.1; employment all 31 geographies show absolute discrepancies (4.5–7.6 percentage points). The V3 report provides magnitudes, not value directions or source values. These observations must NOT be certified or overwritten based on current evidence. Exact-provider replays, local historical-row provenance, flag interpretation and NUTS vintage remain separate acceptance gates.

After merging, perform a read-only rerun, review the newly selected total-education unemployment cohort, and inspect the employment rate mismatch with exact raw local-versus-provider values **only in a controlled local diagnostic** if necessary; never infer the cause from uniformity alone.
