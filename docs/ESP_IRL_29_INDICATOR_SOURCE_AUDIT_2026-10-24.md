# Spain–Ireland: 29-indicator source-audit register (2026-10-24)

Values below were read from AUGUR's local comparison screen, **not a fresh DB export**. Registration is not certification; exact-value validation is reported separately. No database writes.

| # | Indicator | ESP | IRL | Year | Source | Status |
|---:|---|---:|---:|---:|---|---|
| 1 | Fertility | 1.10 | 1.47 | 2024 | EUROSTAT | Exact pending |
| 2 | Median age | 44.9 | 38.4 | 2023 | UN WPP | Exact pending |
| 3 | Net migration | 96630 | 35417 | 2025 | WORLD BANK | IRL exact match |
| 4 | Age 65+ | 20.7% | 15.7% | 2025 | EUROSTAT | Exact pending |
| 5 | Population | 49590099 | 5510565 | 2026 | EUROSTAT | WB 2025 differs by source/year |
| 6 | PM2.5 mortality | 28 | 6 | 2023 | EUROSTAT | Modelled; exact pending |
| 7 | Gov debt | 100.7% | 32.9% | 2025 | EUROSTAT | Exact pending |
| 8 | Rent price index | 113.6 | 173.6 | 2025 | EUROSTAT | Not monthly rental price |
| 9 | Housing cost overburden | 7.2% | 5.3% | 2025 | EUROSTAT | Exact pending |
| 10 | Real house price index | 142.6 | 151.2 | 2025 | EUROSTAT | Exact pending |
| 11 | Life expectancy | 83.7 | 82.4 | 2023 | UN WPP | Exact pending |
| 12 | Tertiary education 25–34 | 52.5% | 66.8% | 2025 | EUROSTAT | Rounded 52/67 corroborated |
| 13 | Unmet medical needs | 2.3% | 5.1% | 2025 | EUROSTAT | Exact pending |
| 14 | Internet access | 97.4% | 95.5% | 2025 | EUROSTAT | Exact pending |
| 15 | Employment 20–64 | 72.4% | 80.2% | 2025 | EUROSTAT | Exact both corroborated |
| 16 | Employment/population 15+ | 51.5% | 61.8% | 2025 | WORLD BANK | Different age definition from above |
| 17 | Real GDP total | 1.47T | 572.66B | 2025 | WORLD BANK | Exact pending |
| 18 | GDP/hour PPP | 62.4 | 145.1 | 2025 | OECD | Exact and PPP base pending |
| 19 | IMF unemployment | 10.5% | 4.7% | 2025 | IMF | LUR provenance and unit review |
| 20 | Eurostat unemployment | 10.5% | 4.7% | 2025 | EUROSTAT | Duplicate construct, not independent outcome |
| 21 | Actual individual consumption | 92.0 | 100.0 | 2025 | EUROSTAT | ES integer 92 corroborated |
| 22 | Real GDP per capita | 29763 | 104417 | 2025 | WORLD BANK | Exact pending; Ireland GDP caution |
| 23 | HICP inflation | 2.7% | 2.1% | 2025 | EUROSTAT | Exact pending |
| 24 | Household price level | 90.9 | 138.1 | 2024 | EUROSTAT | HIGH: vintage/revision mismatch |
| 25 | IMF inflation | 2.7% | 2.1% | 2025 | IMF | Unit and vintage pending |
| 26 | WB inflation | 2.7% | 2.2% | 2025 | WORLD BANK | CPI versus HICP caution |
| 27 | Real GDP growth | 2.8% | 12.3% | 2025 | IMF | Actual cutoff and vintage pending |
| 28 | Intentional homicide | 0.7 | 0.7 | 2024 | EUROSTAT | Unrounded source pending |
| 29 | Energy dependency | 68.9% | 79.5% | 2024 | EUROSTAT | Exact pending |

## Evidence batches

**Eurostat (18 rows):** The 2025 employment rates ESP 72.4 / IRL 80.2 match exactly in the official cross-European Destatis table: https://www.destatis.de/Europa/EN/Topic/Key-indicators/LabourMarket.html . Eurostat's 2025 tertiary attainment is about ESP 52 / IRL 67, but tenths are not yet verified: https://ec.europa.eu/eurostat/databrowser/view/sdg_04_20/default/table?lang=en . AIC Spain 2025 at integer 92 is corroborated at https://ec.europa.eu/eurostat/statistics-explained/SEPDF/cache/1809.pdf . **Household price level requires vintage investigation**: provisional 2024 ES 91.0/IE 138.1 (https://site-test.nsi.bg/en/statistical-data/112/369); 2024 updates published December 2025 ES 91.3/IE 136.8 (https://www.nsi.bg/index.php/en/statistical-data/109/360). AUGUR screen ES 90.9/IE 138.1: mixed vintage is possible but not proven. Official series: https://ec.europa.eu/eurostat/databrowser/view/tec00120/default/table?lang=en . Homicides source confirms period coverage through 2024, not exact country decimals: https://ec.europa.eu/eurostat/databrowser/view/crim_off_cat/default/table?lang=en .

**World Bank (4 rows):** IE 2025 net migration 35,417 is an exact match to the country profile https://data.worldbank.org/country/IE . WB 2025 population ES 49,355,143/IE 5,484,367 differs from AUGUR's Eurostat **2026** values; different years/sources are not a numerical contradiction: https://data.worldbank.org/indicator/SP.POP.TOTL?locations=EU . Other WB figures need exact API verification.

**IMF (3 rows):** WEO LUR, PCPIPCH and NGDP_RPCH require exact release vintage, UNIT, actual/forecast cutoff. The official workbook adapter blocks LUR when UNIT is unverified; the UI may reflect earlier ingestion from a different path. No automatic replacement.

**OECD (1 row):** GDP/hour 2025: PPP and base-price contract not independently verified. The Irish GDP distortion is a major interpretation caveat.

**UN WPP (2 rows):** 2023 life expectancy/median age are estimates, not administrative registers; WPP revision and exact values pending.

## Follow-up and acceptance

- Independently confirmed numeric matches so far: ESP and IRL Eurostat-derived employment 20–64; WB net migration IE. Rounded corroboration for education and AIC ESP. All remaining value pairs are **unverified**, even if their dataset is legitimate.
- Highest priority: read-only local evidence/provenance export with dataset ID, unit, period, source update/retrieval date and dimensions; compare exact country observations against official APIs and source vintage. Prioritize 2024 PPP household price-level revision, 2025 health/housing, IMF LUR and Irish productivity.
- Do not count IMF/Eurostat unemployment or three inflation figures as independent causal outcomes; rates/indices have distinct units and populations. Housing overburden is not market rent affordability.
- No claim of post-merge local application acceptance or source-wide 29/29 numerical certification.
