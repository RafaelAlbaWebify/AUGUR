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

## Country coverage

The first validated multi-country slice is:

- Spain (ESP)
- Portugal (PRT)
- Ireland (IRL)

All five core providers have been successfully synchronized for these countries.

## Planned source expansion

Future dimensions require additional primary sources, likely including:

- housing affordability / housing cost burden
- health and education outcomes
- fiscal structure beyond gross debt
- energy and strategic resilience
- more current or more granular labour-market / occupational earnings evidence
- migration and legal eligibility
- national statistical agencies where harmonized supranational series are insufficient

Every added source must preserve provenance, source date, canonical mapping, and observation type.
