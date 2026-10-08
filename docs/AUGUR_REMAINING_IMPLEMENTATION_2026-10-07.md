# AUGUR Remaining Implementation — 2026-10-07

Status: **core analysis operational / full readiness blocked by external calibration**

This document records only remaining work after P0/P1/P2 completion and current P3 preparation. It distinguishes implementable product work from external-access/data dependencies so AUGUR does not repeatedly rediscover the same boundaries.

## 1. TTV — final readiness blocker

Current state:

- bounded TTV v1 scope implemented;
- temporal gates are supported or scope-bounded except external calibration;
- observation definitions are frozen;
- opt-in development observation lifecycle implemented;
- anonymized development exchange implemented;
- calibration diagnostics implemented;
- protocol state is definitions frozen / acceptance criteria pending.

Remaining:

- collect a representative development sample;
- use development evidence to predeclare acceptance criteria;
- freeze immutable calibration protocol version;
- collect a true untouched holdout under the frozen protocol;
- evaluate holdout;
- only if accepted, assign TEMPORAL_MODEL_VERSION and allow full ready=true.

This work cannot be honestly completed with synthetic or retrospectively tuned cases.

## 2. Detailed skill and language demand

Current state:

- ESCO taxonomy active;
- EURES shortage/surplus active;
- Cedefop STAS active;
- Cedefop CLSSI active;
- Cedefop OJA imbalance active;
- Skills-OVATE detailed skill/language shares remain access-gated.

Remaining:

- obtain reproducible Skills-OVATE / Eurostat microdata access, or
- configure a provider that supplies structured skills/languages from postings under a defensible methodology.

AUGUR must not derive employer-demand shares from ESCO relationships.

## 3. Live postings

Current state:

- vendor-neutral live-postings contract implemented;
- provider status exposed explicitly;
- provider absence is non-blocking and never interpreted as zero demand.

Remaining:

- optional controlled provider pilot;
- preferred candidates: Lightcast if commercial access already exists, otherwise Coresignal for a self-service pilot;
- validate deduplication, geography, occupation mapping, skill extraction, language extraction, salary and trend methodology before adoption.

No provider is required for current public-data operability.

## 4. Access-gated public datasets

Current boundaries:

- Cedefop Skills Forecast full spreadsheet requires request/registration;
- Cedefop RESET official page currently returns HTTP 403 to automated discovery and exposes no reproducible download URL;
- Skills-OVATE detailed data are not available through a stable public download/API path.

Remaining:

- integrate these sources only if a reproducible licensed/download path becomes available;
- do not scrape interactive visualizations or guess hidden endpoints.

## 5. Regional occupation-demand granularity

Current state:

- NUTS2 labour, housing, health, connectivity and sector structure active;
- NUTS3 safety active;
- city population and observed PM2.5 active;
- Eurostat regional JVS dataset currently does not cover ES/PT/IE target regions in the inspected period.

Remaining:

- regional occupation-specific demand only when an official/public or configured live-postings source actually supports it;
- do not infer regional occupation vacancy pressure from sector employment alone.

## 6. Environmental-health extension

Current state:

- city observed PM2.5 concentration active;
- EEA PM2.5 premature-death / years-of-life-lost NUTS2/NUTS3 2005-2023 source verified through the official direct-download package;
- live schema inspection passed;
- parser and dedicated DuckDB storage implemented;
- PMD and YLL, published unit, observation status, NUTS level, period and dataset version are preserved;
- regional API exposes environmental-health burden separately from Eurostat regional indicators and from observed city PM2.5 concentration;
- regional UI renders the EEA burden as a separate evidence block;
- regional metric cards now expose up to eight locally stored historical observations with sparklines and latest-change context;
- refresh/start repair flows automatically populate the local EEA evidence store;
- operability reports EEA environmental-health availability and retrieval freshness separately from national readiness;
- live-source smoke validates both inspection and sync.

Remaining:

- no structural implementation blocker remains for this source;
- continue treating attributable health burden and measured concentration as separate evidence;
- never combine concentration, premature deaths or years of life lost into a synthetic environmental score without a separately validated methodology.

## 7. Operational automation

Current state:

- interactive regional selection is now local-only: it never waits for Eurostat to repair missing series;
- interactive city selection is also local-only: missing Urban Audit / EEA data are repaired during explicit sync rather than on click;
- city evidence now extends beyond population with Urban Audit demography, mobility and tourism metrics plus EEA PM2.5 where verified;
- city metrics are grouped by domain in the Overview and remain explicit when Urban Audit has no observation;
- interactive city reads use a single DuckDB connection for latest values plus history;
- live-source smoke probes Oviedo (ES013C) and requires at least one expanded Urban Audit metric beyond population;
- regional and city evidence are cached in backend/client for repeat selections;
- interactive regional cards use local historical series; region selection does not fetch history from external providers;
- explicit city refresh now owns the EEA PM2.5 network update, preventing the previous interaction-time fetch from becoming an evidence-refresh gap;

- core/subnational evidence syncs automated;
- OJA and CLSSI repair automated;
- local missing-evidence repair implemented;
- bootstrap/refresh/start flows increasingly centralized;
- operability reports source freshness and multiple evidence layers.

Remaining:

- continue folding any newly integrated reproducible source into the same automatic repair/refresh path;
- keep SkipSync as a true no-network mode;
- ensure new optional evidence never silently blocks national analysis readiness.

## 8. Product boundary

AUGUR should not add more scoring merely to increase the number of features.

The main remaining product value comes from:

- real external TTV calibration;
- real posting-derived skill/language demand;
- richer regional demand only where evidence exists;
- incremental environmental-health evidence;
- improving explanation/decision support without pretending unavailable evidence exists.


## Live global-baseline validation

GitHub Actions live-source validation on 2026-10-07 confirmed:

- World Bank country discovery returned **217 real countries** after aggregate filtering;
- the full baseline left **217 analyzable countries** in AUGUR;
- World Bank WDI inserted **47,421** national observation rows;
- UN WPP inserted **130,464** demographic/history/projection rows;
- World Bank sample coverage passed for Germany, United States and India;
- UN WPP sample coverage passed for Germany, United States and India;
- IMF DataMapper v2 and v1 both returned HTTP 403 from the GitHub-hosted runner, so CI records this as `source_access_restricted_in_ci` rather than pretending the adapter or country coverage failed;
- the remainder of the live source smoke completed successfully.

These figures validate the global national architecture against live official sources. They do not imply equal indicator depth for every country; `/api/countries/coverage` remains the source of truth for per-country analytical coverage.

## Global geography coverage architecture

Product scope is data-driven rather than hard-coded to the original Spain / Portugal / Ireland validation set.

Implemented:

- `VALIDATION_COUNTRY_ISO3` keeps ESP / PRT / IRL as the regression/readiness gate only;
- World Bank country metadata can dynamically register real countries while excluding statistical aggregates;
- `/api/countries` exposes countries with actual analytical evidence plus the validation set, rather than every discovered-but-empty country;
- `/api/countries/coverage` reports registered versus analyzable country coverage;
- global provider selection is metadata-driven: global sources apply everywhere, Eurostat only to EU members and OECD only to OECD members;
- World Bank, IMF and UN WPP have batched multi-country ingestion paths;
- `sync-global-baseline.ps1` and `refresh-augur.ps1 -GlobalBaseline` provide an explicit global baseline acquisition path;
- product operability remains regression-gated on the validation set, while additional countries expand coverage without becoming global readiness blockers;
- country map metadata includes source-provided coordinates so non-European countries do not default to an irrelevant Europe-only view;
- `geography_registry` separates geography identity from NUTS/Urban Audit assumptions and records country, level and geography system explicitly;
- `/api/geographies/coverage` reports provider-neutral subnational coverage by country/system/level.

Architecture boundary:

- NUTS 2024 and Urban Audit 2024 are European geography providers, not universal AUGUR geography models;
- future non-European regional/city sources must register their native identifiers and hierarchy in `geography_registry` instead of encoding country identity in a code prefix;
- discovery alone does not make a geography analyzable: at least one stored observation is required for the geography/country to be surfaced as analytical coverage;
- missing provider-specific evidence remains explicit and must not be synthesized from unrelated levels.



## OECD source-native regional expansion

AUGUR no longer treats European NUTS/Urban Audit geography as the universal subnational model.

Implemented and live-verified on 2026-10-07:

- OECD Regions and Cities population-density dataset `DSD_REG_DEMO@DF_DENSITY` version 2.4;
- OECD regional population dataset `DSD_REG_DEMO@DF_POP_BROAD` version 2.4;
- OECD TL2 and TL3 are stored as source-native geography levels under `OECD_TL_2024`;
- labeled SDMX CSV was verified live, including `AU1 = New South Wales` and `AU2 = Victoria`;
- live density observations for AU1/AU2 were verified for 2021–2024;
- OECD population and density reuse AUGUR's existing semantic indicator IDs:
  - `regional_population`
  - `regional_population_density`;
- the OECD sync is restricted to registered OECD countries outside the EU so Eurostat remains the preferred regional source for EU countries;
- source-native geography names are persisted in `subnational_observations` and `geography_registry`;
- `GET /api/geographies?country_iso3=...` exposes analyzable source-native regions by country;
- Overview can select source-native regions even before official boundary geometry is integrated;
- regional evidence for OECD TL2/TL3 only exposes actually stored OECD metrics and does not fabricate missing Eurostat indicators;
- sector and EEA environmental-health context remain unavailable for OECD regions unless independently sourced.

Regional labour extension status:

- OECD `DSD_REG_LAB@DF_RATES` v2.4 was live-inspected on 2026-10-08;
- `EMP_RATIO` for ages 15–64, total sex, is published in `PT_POP_SUB` (percentage of population in the same subgroup);
- AU1 (New South Wales) and AU2 (Victoria) returned observed 2021–2024 employment-to-population ratios;
- `regional_employment_to_population_ratio` is now ingested, persisted, synced and exposed in source-native OECD regional evidence;
- OECD publishes regional unemployment as `UNE_RATE` for ages 15–64 and total sex, with unit `PT_LF_SUB` (percentage of the labour force in the same subgroup);
- `regional_unemployment_rate_oecd` is now ingested, persisted, synced and exposed alongside the employment-to-population ratio;
- live validation for New South Wales returned **4.0%** unemployment in 2024;
- the combined `EMP_RATIO+UNE_RATE` regional sync passed live-source validation.




## OECD source-native urban coverage

AUGUR now has a first non-European urban provider based on OECD harmonised city and Functional Urban Area (FUA) statistics.

Implemented:

- geography system `OECD_FUA`, kept distinct from Eurostat Urban Audit;
- source-native OECD CITY and FUA codes are registered in `geography_registry`;
- city and FUA remain separate geographic levels and are not compared interchangeably;
- country identity is resolved against AUGUR's registered ISO2/ISO3 catalog because the OECD FUA territorial datasets do not consistently populate a country field;
- mixed code prefixes such as `AT001C`, `AUS01C` and `CAN01C` are resolved longest-prefix-first to prevent country collisions;
- OECD urban evidence is fetched only during sync/refresh and served locally from DuckDB during interaction;
- the Overview separates source-native regional geographies from source-native urban areas.

Live OECD evidence verified for Australia includes:

- `AUS01C` — Greater Sydney — CITY;
- `AUS01F` — Greater Sydney — FUA;
- 38 Australian CITY/FUA reference codes in the OECD density dataset;
- population density from `DSD_FUA_TERR@DF_DENSITY` v1.1;
- total population from `DSD_FUA_DEMO@DF_AGE_SEX` v1.2;
- total, youth and old-age dependency ratios from `DSD_FUA_DEMO@DF_DEPEND` v1.2.

Dependency measures remain separate:

- total dependency: people aged under 15 plus 65 or over, relative to population aged 15–64;
- youth dependency: people aged under 15 relative to population aged 15–64;
- old-age dependency: people aged 65 or over relative to population aged 15–64.

AUGUR does not collapse these measures into a composite urban score.

Four-country live validation on 2026-10-08 used Australia, Canada, Japan and the United States and produced:

- **9,868** OECD urban observation rows across population density, total population and dependency ratios;
- **698** distinct registered OECD urban geographies across the four countries;
- density coverage on **638** geographies (322 CITY, 316 FUA);
- population coverage on **515** geographies (260 CITY, 255 FUA);
- dependency-ratio coverage on **515** geographies (260 CITY, 255 FUA).

Coverage is intentionally reported per dataset. A geography with density but without population or dependency evidence is not treated as complete, and country-level sync gaps remain explicit.

Next urban expansion candidates must be inspected and validated before integration. OECD FUA labour-market, commuting and environmental datasets are candidates, but no values should be inferred into cities or FUAs from regional TL2/TL3 evidence.


## OECD urban expansion status

AUGUR now treats OECD Functional Urban Areas and cities as a provider-native
urban geography system (`OECD_FUA`) rather than mapping them to Urban Audit
or NUTS.

Implemented and persisted when published:

- city/FUA population;
- city/FUA population density;
- city/FUA total, youth and old-age dependency ratios;
- FUA employment-to-population ratio;
- FUA labour-force participation rate;
- FUA unemployment rate;
- FUA walking access to a public-transport stop within 5, 10 and 15 minutes.

Semantics are level-aware:

- CITY does not expect FUA-only labour or transport-access indicators;
- FUA and CITY remain separate comparable geographic levels;
- unavailable OECD datasets are explicit coverage gaps rather than inferred
  from regional values.

Provider-native geometry architecture is also implemented:

- `geography_geometries` stores source-native GeoJSON plus bounding boxes;
- `/api/geographies/geometry` exposes the geometry as a FeatureCollection;
- Leaflet renders provider-native polygons independently from GISCO/NUTS;
- the official OECD city/FUA shapefile importer validates WGS84, matches
  source codes against `geography_registry`, and never substitutes
  third-party geometry;
- OECD's hosted boundary archives currently return access restrictions from
  GitHub-hosted runners, so geometry availability is reported separately from
  analytical evidence and does not block urban analysis.

Still withheld from production ingestion:

- OECD FUA PM2.5 exposure. The current live source declares micrograms per
  cubic metre with unit multiplier 0, but the Australian time series contains
  abrupt order-of-magnitude discontinuities under otherwise identical
  dimensions. AUGUR will not surface this series until the discontinuity is
  understood.
- OECD FUA economy data for the probed Australian FUAs. The dataset is valid,
  but the probe returns no records; this remains a source coverage gap.

