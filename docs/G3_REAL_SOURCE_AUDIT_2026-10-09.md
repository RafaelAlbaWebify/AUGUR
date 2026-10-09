# G3 — Actual regional evidence audit (2026-10-09)

## Inputs and reproducibility

- Local evidence: user-supplied `AUGUR_GEOGRAPHIC_COVERAGE.json` (26 country/system/level/indicator groups, ESP/IRL/PRT). Values below are **local registered-geography** coverage, NOT official source completeness.
- Code inspected: `backend/app/ingestion/eurostat_regional_health.py`, `eurostat_regional_housing.py`, `eurostat_regional_access_safety.py`, and `eurostat_regional_labour.py` on main as of 2026-10-09.
- Official datasets verified against Eurostat browser pages/metadata on 2026-10-09. Dates listed are observation-year ranges from source pages, not ingestion timestamps.

## Source-by-source findings

| AUGUR indicator | Local observation evidence | Code dataset/filter/unit | Official Eurostat contract and source | Classification / action |
|---|---|---|---|---|
| `regional_hospital_beds_per_100k` | ESP 4/19 regions, latest 2024 | `hlth_rs_bdsrg2`, `unit=P_HTHAB` → `per_100k_people` | Available beds by NUTS2, 1993–2025, per hundred thousand; https://ec.europa.eu/eurostat/databrowser/view/hlth_rs_bdsrg2/default/table | **Unit matches**; local incomplete. Do not claim all 19 have an available observation in 2025 without geo-level API check. |
| `regional_disposable_income_pps_per_capita` | ESP 4/19, latest 2023 | `nama_10r_2hhinc`, `unit=PPS_EU27_2020_HAB`, `direct=BAL`, `na_item=B6N` → `pps_per_person` | Household income by NUTS2, dataset extends to 2024; source page https://ec.europa.eu/eurostat/databrowser/view/nama_10r_2hhinc/default/table | **Contract plausibly aligned**; verify dimensional availability for ES/IE/PT and 2024 specifically. Do not conflate EU-wide latest year with ESP. |
| `regional_household_internet_access` | ESP 4/19, latest 2025 | `isoc_r_iacc_h` regional access source | Households with internet at home, NUTS2, through 2025; https://ec.europa.eu/eurostat/databrowser/view/isoc_r_iacc_h/default/table | **Source verified**; local only 4 regions. Verify the selected internet-access measure and per-region availability; do not infer nationwide coverage. |
| `regional_housing_cost_overburden_rate` | ESP 4/19, latest 2025 | `ilc_lvho07_r`, `unit=PC` | Source ID configured; measure-specific dimensions and regional coverage **not independently verified in this audit** | **Unverified contract**; inspect metadata and actual JSON-stat dimension codes before accepting. |
| `regional_unmet_medical_needs` | ESP 4/19, latest 2025 | `hlth_silc_08_r`, `reason=TXP_TFAR_WLIST`, `unit=PC` | Self-reported unmet medical examination needs **by declared reason** at NUTS2, through 2025; https://ec.europa.eu/eurostat/databrowser/view/hlth_silc_08_r/default/table | **Semantic warning**: displayed indicator must specify selected reason / subgroup; do not present as an unrestricted measure of all unmet needs. Verify reason-code label directly from dimension metadata. |
| `regional_air_passengers_thousands` | ESP 4/19 ever, 2/19 at 2024; other local latest periods 2000 and 2002 | `tran_r_avpa_nm`; source-specific parser and dimension selection must be checked | Air passengers by NUTS2, `unit=THS_PAS` and `tra_meas=PAS_CRD`, published through 2024; https://ec.europa.eu/eurostat/databrowser/view/tran_r_avpa_nm/default/table | **Temporal mismatch**: do not compare 2000/2002 regions with 2024 as peers. Absence may be non-applicability, unavailable source observations, or ingestion gap. |
| `regional_intentional_homicide_rate` / `regional_robbery_rate` | ESP 3/3 locally registered NUTS3; IRL 8/8; PRT 26/26 | `crim_gen_reg`, NUTS3 | Official police-recorded regional crime, with recording/definition differences; https://ec.europa.eu/eurostat/cache/metadata/EN/crim_gen_reg_esms.htm | **Coverage interpretation defect**: Spain's 3/3 cannot be presented as full-country NUTS3 coverage (official GISCO NUTS3 catalog has 59 ES codes). Methodological comparability caveat is mandatory. |

## Cross-country findings needing exact-code reconciliation

- ESP: 19 official GISCO 2024 NUTS2 and 59 NUTS3 catalog entries; only 3 local NUTS3 registered for the crime groups.
- IRL: official 2024 NUTS2 catalog 3 codes; local registered count 5 for labour groups. Two locally registered labour geographies have last period 2011 while three have last period 2025. **Possible boundary-vintage mixing**; do not diagnose definite duplicates without codes.
- PRT: official 2024 NUTS2 catalog 9 codes; local registered count 12 for labour groups. Three end 2018 while nine have observations through 2025. **Possible legacy geography entries**; do not silently treat the 12-region union as contemporaneous 2025 coverage.
- IRL: city population last observation years 2011/2016 for five locally registered cities; must not display as contemporary city population.
- ESP: income, hospitals, internet, housing burden, medical need all 4/19, but coincidence of count alone **does not establish common origin** or a single ingest bug. Exact per-code and source-response inspection is required.

## Confirmed versus unverified

**Confirmed:** actual local counts/period distributions in the uploaded JSON; code's configured source IDs and explicit filters; official scope, published global year span and selected unit for inspected datasets. **Not confirmed:** values themselves, data rows for each ES/IE/PT code, source JSON-stat data flags, exact source-unit compliance for all indicators, detailed OECD coverage, cause of omissions, or successful repair.

## Next testable engineering sequence

1. Inspect upstream JSON-stat dimensions + actual non-null values for the affected country/indicator pairs, preserving geo code, period, source status flag, unit, and dataset ID.
2. Compare source-specific valid codes for the same period against GISCO NUTS2024 geography, **not** across vintage eras.
3. Separate statuses: no official source value, non-applicable, ingestion error, outdated period, historical code, unverified.
4. Rectify any verified adapter dimension/filter mismatches with tests using captured legitimate source metadata; no synthetic production observations.
5. Only then report improvement in eligible same-year coverage, and annotate UI cards with source time, units and limitations.

**Disposition:** G3 evidence audit performed at dataset-contract and local-distribution level. Full observational / per-code official API reconciliation remains **not yet verified**.
