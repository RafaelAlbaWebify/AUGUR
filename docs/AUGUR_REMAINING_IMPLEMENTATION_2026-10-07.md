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
- refresh/start repair flows automatically populate the local EEA evidence store;
- live-source smoke validates both inspection and sync.

Remaining:

- no structural implementation blocker remains for this source;
- continue treating attributable health burden and measured concentration as separate evidence;
- never combine concentration, premature deaths or years of life lost into a synthetic environmental score without a separately validated methodology.

## 7. Operational automation

Current state:

- interactive regional selection is now local-only: it never waits for Eurostat to repair missing series;
- regional evidence is cached in backend and revisited regions are cached in the overview client;

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
