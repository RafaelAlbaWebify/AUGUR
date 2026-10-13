# G3 — Real local coverage and age audit (2026-10-13)

## Evidence and limitations

Operator exported `AUGUR_G3_OBSERVATIONS.json` and `AUGUR_G3_GEOGRAPHIES.json` from the active post-G2 local DuckDB database on 2026-10-13. Inventory: **206 registered geographies**, **50 country/system/level/indicator/source/unit provenance groups**, **7,915 subnational observations** across three countries. The export scripts count only registered observations and do not establish official provider completeness, code boundary vintage, or current-year values for each geography. There are **0 unregistered observation geographies** reported. All registered geographies have `boundary_version_verified: false`; this field is not a finding that all labels are wrong.

## Verified on-disk evidence

- ESP NUTS2: 19/19 locally registered geographies carry employment, unemployment, GDP per capita, population, population density at some period. The six other registered indicators (air passengers, disposable income, hospital beds, household internet, housing cost overburden, unmet medical needs) each cover only **4/19**. Coverage at any time is not same-year comparability. Source-adapter defect vs official non-availability remains unverified.
- IRL NUTS2: 3/3 current catalog geographies have the same five fundamental indicators, plus 2 historical `NUTS_UNSPECIFIED` geographies with employment and unemployment periods 1999–2011.
- PRT NUTS2: 9/9 current catalog geographies have employment and unemployment; 3 historical `NUTS_UNSPECIFIED` geographies have those two indicators for 1999–2018. No local GDP/population NUTS2 group shown in the inventory.
- NUTS3 crime groups: ESP **3** locally registered geographies, IRL **8**, PRT **26**. **Do not claim countrywide crime coverage on the basis of registered-geography denominator.** These crime series also require comparability caveats.
- Urban-city latest group-wide observation periods: ESP transit monthly pass **2012**, public-transport commute **2011**, walk commute **2011**, tourism beds/nights **2020**; IRL population **2016**, median age **2011**, commute **2011**, car registrations **2002**, tourism beds/nights **2002**; PRT monthly pass **2016**, commute **2011**, tourism beds/nights **2020**. These dates are a maximum across each national group, not a guarantee for every city.
- Actual 2026-10-13 ingestion timestamp is not the reference year. Do not market obsolete observations as current.
- Source `unit` strings are present and coherent at inventory level; no full observed-value or upstream JSON-stat semantic audit was performed. Prior code-level review flags `regional_unmet_medical_needs` selected reason/subgroup label as an interpretation risk.

## G3 MVP acceptance criteria

1. **High priority:** UI/API makes each displayed city's *actual observation year*, source and stale status legible; applies no invalid "current" or "latest" freshness inference from ingestion timestamps. Add tests for year 2002/2011/2016 cases and uneven per-city ages. Never silently impute values.
2. **High priority:** If country indicator coverage is partial, expose numerator, denominator and denominator scope. Do not imply national geographic completeness from 3/3 registered Spanish crime regions or merge incompatible reference periods.
3. **High priority:** Confirm filter/unit semantics for health/unmet needs and other decision-driving datasets against actual upstream metadata before broad comparisons; maintain `unknown` where not verified.
4. **Retain:** G2 vintage corrections; label historical NUTS_UNSPECIFIED separately and do not certify surviving same-code 2024 boundary vintage from membership.
5. **No MVP mandate:** Import every city/indicator, repair provider non-availability, or externally calibrate TTV.

Disposition: **G3 audit is complete at local inventory level; G3 functional mitigation implementation and real in-app acceptance remain open.**

## Confirmed Eurostat semantic issue — 2026-10-13

The `regional_unmet_medical_needs` indicator uses `hlth_silc_08_r` with `reason=TXP_TFAR_WLIST`, `unit=PC`, `freq=A`. Eurostat defines this reason as **too expensive, too far to travel, or waiting list**, not unmet medical needs for any reason (`ANY` is a distinct category). Regional evidence presentation now names the selected reason explicitly to avoid incorrect generalization. Primary sources: https://ec.europa.eu/eurostat/databrowser/view/hlth_silc_08_r/default/table and https://ec.europa.eu/eurostat/cache/metadata/en/hlth_silc_01_esms.htm . This checks *semantic interpretation*, not correctness of all stored values or every source dimension; broader upstream contracts require further audit.
