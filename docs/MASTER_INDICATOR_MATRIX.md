# AUGUR master indicator coverage matrix — v1 (2026-10-10)

This is a **product requirements and evidence-gap matrix**, not a claim that missing official observations exist. The reproducible declaration inventory is generated with `python -m scripts.export_indicator_inventory --output ../national_indicators.json` from `backend/`. Local observation availability must be assessed separately.

**Evidence states**: D = declared in national `INDICATORS` catalog; P = related pipeline/partial metric but adequacy not validated; G = priority gap needing new implementation and source qualification. Levels: N national, R regional, C city, L legal/rules for profile. A proposed source is not an ingested verified dataset.

| Priority | Decision domain | Necessary measures | Present baseline | Target scope | Preferred sources / constraint |
|---|---|---|---|---|---|
| P0 | Growth and productivity | Real GDP/capita trend, productivity/hour, real wages, investment, median household income | D: GDP, GDP/capita, growth, GDP/hour; wages incomplete | N/R | Eurostat, OECD, IMF; compare in constant prices or PPP as appropriate |
| P0 | Work opportunities | Employment/unemployment, occupation demand, vacancies, salary distribution, skills and language demand | D/P: labour indicators, EURES, Cedefop; local skills demand gated | N/R/C | Eurostat LFS/SES, OECD, EURES, Cedefop; do not infer job postings from ESCO taxonomy |
| P0 | Personal taxes and take-home pay | Tax wedge; effective PIT; SSC; income after tax for individual/household; self-employed and corporate taxes | P: FinancialFit net-earnings benchmark; **not enough** for personalized tax | N/L (+ R/C tax variations) | OECD Taxing Wages, Revenue Statistics, official tax administrations; legal rules and individual calculation versioned separately |
| P0 | Housing affordability | Median rent, purchase price, rent/net earnings, price/income, cost overburden, transaction volume, energy bills | D: house/rent price indices and overburden; P: regional housing | N/R/C | Eurostat/OECD and national land registries/statistics; announced asking prices are not transaction prices |
| P0 | Migration and residence rights | Entry and work entitlements, visa criteria, dependents, residence duration, recognition of qualifications | P: LegalFit (EU status etc) | N/L | Official government/immigration portals, EUR-Lex/Your Europe; version by nationality, pathway and date |
| P1 | Business freedom | Regulatory quality, start-up administrative burdens, business taxation, contract enforcement | G | N (+ regional rules where grounded) | WGI, World Bank B-READY, official licensing/tax rules; survey/index limitations |
| P1 | Institutions and civil liberties | Rule of law, government effectiveness, corruption control, political/civil rights, judicial performance | G | N | World Bank WGI, EU Justice Scoreboard; indices explicitly distinct from observed facts |
| P1 | Healthcare | Life expectancy, preventable/treatable mortality, access unmet need, beds, provider density, waiting times | D: life expectancy/unmet need; P: regional beds | N/R/C where available | OECD Health Statistics, Eurostat, health authorities; beds are not waiting times |
| P1 | Safety | Homicides, robbery, victimization, safety perceptions | D: homicide; P: regional crime | N/R/C | Eurostat/UNODC, police reports, official surveys; law/reporting differences matter |
| P1 | Education | Attainment, learning outcomes, childcare provision/cost, schools accessibility | D: tertiary attainment | N/R/C | OECD PISA, Eurostat, official education and municipal statistics |
| P1 | Transport and access | Commute time, public transit accessibility, mode share, car dependency, air connectivity | P: OECD FUA, regional air passengers | R/C | OECD FUA, Eurostat, municipal travel surveys |
| P1 | Cost of living | AIC purchasing power, CPI, essentials basket, utility/energy cost, price levels | D: inflation, AIC, price index | N/R/C where available | Eurostat PPP/HICP, OECD price databases; no extrapolation of local costs from country index |
| P1 | Environment/climate | PM2.5, attributable mortality, heat exposure, flood/wildfire risk, noise, green space | D/P: mortality, city PM2.5 and FUA green area | N/R/C | EEA, Copernicus, OECD; modelled burden distinct from measured pollution |
| P2 | Demography and long-term sustainability | Fertility, old-age dependency, migration, population change, public debt | D: demography and public debt | N/R/C | UN WPP, Eurostat, OECD/IMF; forecast separate from history |
| P2 | Social conditions | Poverty after housing, inequality, social protection, social connection, life satisfaction | G (partial material welfare) | N/R/C if representative | Eurostat EU-SILC, OECD Better Life and regional well-being |
| P2 | Entrepreneurship / investment | Business births/survival, investment, financing access, digital public services | G | N/R | Eurostat Structural Business Statistics, World Bank B-READY, national business registries |

## Critical boundaries

- **Country → region → city** is a hierarchy of legal context, not a license to copy national observations into city charts.
- A **source dataset existing** is not proof it has a value for any particular ES/IE/PT geography and year.
- Raw observations, published composite indices, binding legal rules, and AUGUR's derived calculations must be explicitly separated.
- Each ingested series needs dataset ID, exact selection dimensions, unit, period, source and applicable geography codes; each rule needs jurisdiction, eligibility, effective dates and provenance.
- Avoid a single opaque “best place” score. Provide dimension-by-dimension objective trends first and individual feasibility separately.

## Next bounded implementation batch

1. **Fiscal feasibility**: authoritative tax-wedge and net-pay source contract; clarify household scenarios and tax residency rather than adding a generic low-tax score.
2. **Housing affordability**: real rents/prices and net-wage affordability across available geographical scales, with unit/period harmonization and sparse-data display.
3. **Institutions**: versioned WGI source contracts with index caveats; B-READY only when source country coverage verified.
4. **Migration pathways**: authoritative per-nationality residence/work rules with effective-date audit.
5. **Real acceptance**: for ES/IE/PT, prove at least one authentic source-backed end-to-end country and regional/city use case for each P0 domain; record absent observations instead of synthesizing them.

**Status:** requirements gap mapping complete; source contracts and product evidence acceptance are not. This file complements [ROADMAP.md](ROADMAP.md) and [VALIDATION.md](VALIDATION.md).
