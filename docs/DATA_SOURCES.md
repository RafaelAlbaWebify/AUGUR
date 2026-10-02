# AUGUR Data Sources

AUGUR prefers official or primary statistical sources and retains source provenance for every observation.

## World Bank — World Development Indicators

Role:

- broad cross-country historical baseline.

Current canonical indicators include:

- population
- real GDP
- real GDP per capita
- unemployment
- employment/population ratio
- CPI inflation
- fertility
- population 65+
- net migration

## Eurostat

Role:

- preferred European observations where suitable canonical data exists.

Current coverage includes:

- population
- unemployment
- fertility
- population 65+
- employment rate 20–64
- HICP annual inflation
- public debt / GDP

Eurostat has higher source priority than World Bank for overlapping EU canonical observations.

## OECD

Role:

- structural productivity evidence.

Current coverage:

- GDP per hour worked, PPP / constant-price productivity series.

## IMF World Economic Outlook

Role:

- official macro forecasts.

Current coverage:

- real GDP growth
- average consumer-price inflation
- unemployment

AUGUR stores forecast-period values separately from historical observations.

## UN World Population Prospects 2024

Role:

- long-horizon demographic estimates and projections.

Current coverage:

- population
- fertility
- median age
- life expectancy

The medium variant is used for the official demographic baseline.

## Eurostat Structure of Earnings Survey 2022

Role:

- structural local-employment earnings reference for Personal Fit.

Dataset:

- `earn_ses22_21` — mean monthly earnings by sex, age and ISCO-08 occupation group.

AUGUR requests:

- gross earnings (`ERN`);
- euro (`EUR`);
- total sex;
- total age;
- enterprises with 10 or more employees;
- occupation groups retained separately by ISCO-08.

This evidence is stored outside the normal country observation series because occupation is an additional analytical dimension.

SES is four-yearly. The current implemented reference year is 2022, so AUGUR presents it as structural earnings evidence, not a current salary quote or job offer.

## Eurostat annual net earnings

Role:

- national net-income benchmark for local-employment FinancialFit.

Dataset:

- `earn_nt_net` — annual net earnings.

Current standard case:

- frequency: annual;
- currency: euro;
- earnings structure: net;
- earnings case: `P1_NCH_AW100` — single person without children earning 100% of the average wage.

This is a national average-worker benchmark. AUGUR does not apply it as a tax conversion factor to the occupation-specific gross SES value and does not describe it as occupation-specific net pay.

The dataset currently covers observations through 2025.

## Country coverage

The first validated multi-country slice is:

- Spain (ESP)
- Portugal (PRT)
- Ireland (IRL)

All five core providers have been successfully synchronized for these countries.

## Planned source expansion

Future source expansion remains most relevant for:

- more granular housing affordability and local housing costs;
- deeper health and education outcomes;
- fiscal structure beyond gross debt;
- broader strategic resilience indicators;
- more current and occupation-specific labour-market earnings and hiring evidence;
- verified country-specific migration and legal eligibility;
- national statistical agencies where harmonized supranational series are insufficient

Every added source must preserve provenance, source date, canonical mapping, and observation type.


## ESCO language-skill metadata

Role:

- identify ESCO skills and knowledge concepts classified as language-related;
- preserve essential/optional occupation-skill relationships for LanguageFit.

The ESCO CSV package includes a `languageSkillsCollection` file. AUGUR imports that collection as classification metadata and combines it with occupation-skill relations.

This evidence describes language-related skills associated with an occupation. It does not provide a CEFR level and is not treated as a legal or employer-specific language threshold.


## Eurostat labour-market transition baseline

Role:

- experimental timing evidence for local-employment TTV validation.

AUGUR stores this evidence separately from country macro observations.

The current implementation uses a country-level unemployment-to-employment transition probability and converts the quarterly transition probability into cumulative 50% and 80% transition horizons under a constant-quarterly-hazard assumption.

AUGUR now ingests all published age classes from the selected dataset. When the profile age maps to an available Eurostat group, that group is preferred; otherwise the model falls back explicitly to the 15–74 aggregate. Profiles outside the dataset's 15–74 population are withheld rather than extrapolated.

Important limitations:

- country-level, not occupation-specific;
- not an individual probability of receiving a job offer;
- not a guarantee of employment;
- the constant-hazard transformation is an AUGUR modelling assumption;
- the resulting weeks are candidate temporal evidence only and are not published as TTV while the temporal model remains unversioned.

## Cambridge English guided learning hours

Role:

- planning evidence for language-progression timing.

AUGUR uses published cumulative guided-learning-hour ranges by CEFR level. The current target is AUGUR's B2 professional-work heuristic.

Calendar weeks are only calculated when the user explicitly supplies expected language-study hours per week.

These ranges are learning guidance, not guarantees of elapsed calendar time or employer language requirements.


## EURES labour shortages and surpluses

Role:

- versioned labour-market shortage/surplus evidence for CareerFit.

AUGUR keeps EURES market evidence in:

`backend/app/evidence/eures_lmi_2025.json`

The manifest deliberately separates two evidence layers.

### Broad country evidence

The broad fallback layer is retained from the implemented EURES country labour-market pages and represents 2024 conditions.

It provides broad shortage/surplus occupation groups for Spain, Portugal and Ireland.

Broad evidence is useful context, but it does **not** count as complete CareerFit market evidence for TTV.

### ISCO unit-group evidence

The more specific layer is transcribed from the official **Report on labour shortages and surpluses 2025 — Annex**, published in 2026 and describing 2025 conditions.

Current verified unit-group coverage includes 13 ICT ISCO-08 groups:

- 2511, 2512, 2513, 2514, 2519;
- 2521, 2522, 2523, 2529;
- 3511, 3512, 3513, 3514.

Unit-group evidence takes precedence over the broad fallback whenever both are available.

This matters because broad groups can contain occupations with different country outcomes. For example, the latest annex classifies ISCO 3512 user-support technicians as surplus in Portugal but does not classify the same occupation as shortage or surplus in Spain or Ireland.

The annex can also report the same occupation as both shortage and surplus within one country. AUGUR preserves that as `mixed_shortage_and_surplus` rather than forcing one direction.

Current limitations:

- only selected ICT unit groups have been transcribed into the verified layer;
- `full_occupation_coverage` therefore remains false;
- national methodologies contributing to EURES can differ;
- a shortage signal does not guarantee individual vacancy availability;
- location, seniority and employer-specific requirements remain separate evidence gaps.

CareerFit returns provenance for the layer actually used: evidence ID, rule version, report year, conditions year, source URL and scope. Updating unit-group evidence should update the manifest rather than CareerFit logic.


## Eurostat occupation vacancy rates

Role:

- supplemental unmet-demand context for CareerFit.

Dataset:

- `jvs_q_isco_r21` — quarterly job-vacancy statistics by occupation and NACE Rev. 2.1 activity.

AUGUR ingests the job vacancy rate (`JVR`) for national aggregate activity, total establishment size and seasonally adjusted data. Only ISCO major groups (`OC1`–`OC9`) are retained.

This evidence is intentionally broader than the resolved ESCO occupation. It is therefore labelled `context_only`.

A vacancy rate:

- does not replace EURES shortage/surplus classification;
- does not make CareerFit evidence complete;
- does not change the TTV viability gate;
- is not a job-finding probability;
- is not converted into weeks-to-employment.

Its purpose is to expose recent official unmet-demand context alongside the more occupation-specific EURES evidence.
