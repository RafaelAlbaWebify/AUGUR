# Global expansion evidence contract — 2026-10-10

**Architecture rule:** no indicator, territory, source selection or unit can assume Spain, Portugal or Ireland are the only eligible locations. A country's absence from a provider dataset is **missing coverage**, not zero and not a reason to fabricate a substitute.

## Contract and automated gates

`backend/app/services/global_evidence_contract.py` defines `EvidenceContract`, `validate_observation` and `coverage_matrix`. These are source/level/geography-system/period/unit guards for observations, not a worldwide data supplier.

- **Territory:** require explicit `country_iso3`, `geo_code`, `geo_level` and `geography_system`. Do not reuse a country estimate as city data or silently mix NUTS vintages with OECD territorial classifications.
- **Series:** require indicator, source, dataset, unit and period; do not compare prices per square metre with monthly household rent, nominal EUR with PPS, or statistics for different family types.
- **Coverage:** registered eligible locations may be observed, missing or incompatible; missing is not zero. Do not treat a partial registered geography catalog as the official universe.
- **Providers:** Eurostat covers EU/EEA-related statistical regions, OECD covers different country/geographic sets, World Bank/IMF are mostly national, and official national statistical offices provide localized price/housing evidence. Data source eligibility is explicit and may differ across places.
- **Legal/tax:** immigration eligibility and individual tax liability depend on nationality, household circumstances, residence and date; statistical averages alone cannot resolve those rules.
- **Operation:** a new country requires an authoritative geography registry, compatible provider series with documented dimensions, observed dates/units and negative-path tests before acceptance. The framework cannot conjure global coverage.

## Expansion acceptance matrix

1. Discover coverage by provider, dataset, geography system, level and country without hardcoded ES/IE/PT loops.
2. Separate **available**, **source missing**, **not applicable**, **old geography version**, **incompatible unit**, **source error**, and **not yet ingested** as evidence permits; do not falsely classify from missingness alone.
3. Reject incompatible units, geographies, timestamps and provider-dataset combinations before building comparative metrics.
4. Display evidence status and period in the API/UI; do not label an entire country/region/city fully covered because a local subset has complete data.
5. Run the same contract/regression checks for a non-EU test location and a city to expose geographic assumptions.
6. Require source-backed matching nominal rents, housing specifications and disposable cash income for an actual rent-to-income percentage. Current regional housing data support descriptive context only.

## Integration state

The generic contract is **implemented and CI-testable**, but existing ingestors still contain provider-specific geography and pilot-country restrictions. Gradual migration of each ingestion pipeline to this contract, plus official-provider discovery and real international integration smoke, is required before claiming automatic worldwide onboarding. Pilot ES/PT/IE remain the verification set, not the future product boundary.

**Next milestone:** wire country-agnostic metadata/configuration into the ingestion/orchestration layer, then run an OECD-supported non-EU country + local city/region acceptance with authentic data and preserve absence honestly.
