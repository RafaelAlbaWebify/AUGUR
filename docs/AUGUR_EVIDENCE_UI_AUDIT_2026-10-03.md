# AUGUR Evidence, Insight & UI Audit — 2026-10-03

## Purpose

AUGUR should help a user answer four distinct questions without collapsing them into one opaque score:

1. **How is a country/region doing now, and is it improving or deteriorating?**
2. **Where is my occupation genuinely in demand, and which skills/languages increase my options?**
3. **What is likely to change over the next few years, based on official forecasts and clearly-labelled model assumptions?**
4. **Given my own profile and priorities, which locations are a robust fit for me?**

The recommended product architecture therefore separates **objective country trajectory**, **labour-market intelligence**, and **personal fit**.

---

## 1. Current AUGUR evidence inventory

### Countries currently supported

- Spain (ESP)
- Portugal (PRT)
- Ireland (IRL)

This is adequate for product validation but not yet enough for a general "best place to live/work" tool.

### Current country indicators

AUGUR currently defines 24 indicators across seven dimensions:

| Dimension | Current indicators | Main source families |
|---|---|---|
| Prosperity | household price level, real GDP growth, inflation, real GDP/capita | Eurostat, IMF, World Bank |
| Productive capacity | unemployment, employment rates, real GDP, GDP/hour | Eurostat, IMF, OECD, World Bank |
| Housing | real house price index, rent index, housing-cost overburden | Eurostat |
| Demography | population, fertility, 65+ share, median age, net migration | UN WPP, World Bank, Eurostat |
| Human systems | life expectancy, tertiary attainment | UN WPP, Eurostat |
| Fiscal sustainability | public debt/GDP | Eurostat |
| Strategic resilience | energy import dependency | Eurostat |

### Personal-fit evidence

- **LegalFit:** EU free-movement framework from European Commission / Your Europe.
- **LanguageFit:** declared CEFR + country labour-market language + ESCO occupation-language relationships; B2 is explicitly an AUGUR heuristic.
- **CareerFit:** ESCO occupation/skill matching + EURES/ELA shortage/surplus evidence + Eurostat experimental vacancy context.
- **FinancialFit:** Eurostat SES occupational gross earnings, national net-earnings benchmark, household price-level comparison.
- **TTV:** Cambridge guided-language hours, Eurostat labour transitions, and an experimental dependency graph.

---

## 2. Source quality audit

Grades below rate suitability **for AUGUR's stated use**, not institutional credibility.

| Evidence | Suitability | Strength | Main limitation for AUGUR |
|---|---:|---|---|
| Eurostat standard statistics | A | Harmonised official EU statistics with metadata | National averages can hide regional variation; some series lag |
| OECD productivity / well-being data | A | Strong harmonisation and international methodology | Current AUGUR ingestion uses very little of the available OECD evidence |
| IMF WEO | A- | Authoritative macroeconomic forecasts and historical series | Forecasts are revised and are not personal/local outcomes |
| UN WPP | A- | Leading demographic projections; explicit variants | Medium variant is a projection scenario, not a certainty |
| World Bank WDI | A- | Broad, stable historical coverage | Some indicators are modelled/lagged; Eurostat is often better for EU detail |
| ESCO v1.2.1 | A as taxonomy | Official occupation/skill graph, multilingual, ISCO-linked | It describes occupations and skills; it does **not** measure current employer demand |
| ELA/EURES unit-group shortage/surplus evidence | B+ | Official occupational imbalance evidence | Coverage is partial; shortages can be regional; methodology can differ by country |
| EURES broad occupation groups | B | Useful context and official source | Too coarse for an individual job decision |
| Eurostat experimental JVR by occupation/region | B+ experimental | Combines official JVS with OJA/LFS detail | Online-ad coverage and occupational/portal bias; explicitly experimental |
| Eurostat SES occupational gross earnings | B+ | Official structural earnings data by broad occupation | Broad ISCO groups, lagged, enterprises 10+, gross rather than personal net pay |
| Eurostat national net-earnings reference | B for personal fit | Transparent official benchmark | Standard national worker case, not occupation/region/person-specific |
| Eurostat unemployment-to-employment transition evidence | B- for TTV | Official empirical transition evidence | Country/age-level rather than occupation-specific; current TTV use is experimental |
| Cambridge guided learning hours | B for planning | Published CEFR learning guidance | Learning time varies materially by person/context; not labour-market evidence |
| AUGUR scenario envelope | C / experimental | Transparent assumptions | Not empirically calibrated or backtested; must not drive “best future country” conclusions yet |

### Important distinction

A strong institutional source does not automatically produce a strong insight. AUGUR must evaluate:

- source authority,
- exact dataset/definition,
- geography,
- period and revision status,
- comparability,
- missingness,
- measurement uncertainty,
- whether the statistic is objective, survey-based, estimated or experimental,
- and whether the inference made from it is justified.

---

## 3. Audit of current inference quality

### 3.1 Trend engine

The current trend engine:

- computes 1/3/5-year percentage changes,
- classifies direction primarily from the longest available point-to-point change,
- uses a universal 1% threshold for “stable”,
- calculates a 5-year linear slope but does not use it for classification,
- labels confidence high/medium/low mainly from history depth.

This is transparent but too simple for a mature “improving/deteriorating” claim.

### Problems

1. **Universal threshold:** 1% has very different meaning for inflation, life expectancy, debt, unemployment and an index.
2. **Endpoint sensitivity:** a 5-year start/end comparison can ignore volatility and turning points.
3. **No peer context:** improvement from a poor level may still leave a country weak relative to peers.
4. **No statistical confidence:** current “confidence” is evidence depth, not uncertainty around the trend.
5. **No revision risk:** macro series and forecasts can be revised.
6. **Correlated indicator voting:** multiple unemployment/inflation/population measures can effectively count the same construct more than once.

### Recommended trend model

For each indicator expose five separate concepts instead of one overloaded label:

- **Current level** — actual latest value.
- **Recent direction** — robust 3/5y trend.
- **Momentum** — whether the direction is accelerating/decelerating.
- **Peer position** — percentile or distance from comparable countries/regions.
- **Evidence reliability** — source/coverage/freshness/uncertainty.

Use indicator-specific material-change thresholds and robust trend estimators. Avoid automatically treating every statistically measurable increase/decrease as meaningful.

---

## 4. What is missing for “where should I live?”

Eurostat’s quality-of-life framework uses 8+1 dimensions and explicitly combines objective and subjective evidence. OECD regional well-being measures eleven topics and emphasises that country averages are insufficient for how people actually experience a place.

AUGUR should add at least:

### Material living standard
- household disposable income
- personal net-income scenarios
- price levels / purchasing power
- housing-cost burden
- rent-to-income and price-to-income
- energy and transport costs

### Jobs and job quality
- employment/unemployment
- long-term unemployment
- temporary/involuntary part-time work
- hours / work-life balance
- occupation-specific demand
- salary distribution rather than only mean

### Health
- healthy life years
- avoidable/preventable mortality
- unmet medical needs due to cost/waiting/distance
- access to care

### Safety
- homicide / serious crime indicators where comparable
- victimisation / perceived safety where available
- distinguish objective and subjective measures

### Environment / climate
- PM2.5 / NO2 / ozone
- heat exposure and climate risk
- green space where reliable
- energy transition / dependency

### Access and infrastructure
- broadband / digital access
- transport/access to services
- regional accessibility

### Community / subjective well-being
- life satisfaction
- social support/community
- trust/civic engagement when methodologically comparable

### Geography
Move from **country-only** toward **region/city** wherever official data supports it. OECD Regional Well-Being, Eurostat NUTS datasets, EEA air-quality stations/cities and OJA regional data are highly relevant.

---

## 5. What is missing for “what skill or language should I learn?”

ESCO is the correct vocabulary layer but not a demand layer.

Professionals measure labour-market opportunity by combining:

1. **occupation taxonomy** (ESCO/ISCO),
2. **current postings/vacancies**,
3. **skills extracted from postings**,
4. **supply of workers/skills**,
5. **hiring / transition evidence**,
6. **future occupation forecasts**,
7. **salary or wage premium**,
8. **regional demand**,
9. **trend through time**.

### Recommended European stack

#### Tier 1 — public / official
- ESCO — occupation and skill taxonomy.
- Eurostat JVS / experimental occupation-region JVR.
- Cedefop Skills-OVATE — OJA skills and occupations by country/region.
- Cedefop Skills Forecast — future employment by occupation/sector/qualification; demand, supply and imbalances.
- ELA/EURES — shortage/surplus and mobility context.

#### Tier 2 — optional commercial enrichment
- Lightcast or equivalent real-time job-posting intelligence.
- LinkedIn-derived market intelligence when legally/licensably available.

### Skill insight to calculate

For each skill × occupation × region × time window:

- posting demand share,
- YoY demand growth,
- demand relative to worker supply where available,
- salary premium where available,
- number/diversity of employers requesting it,
- co-occurring skills,
- whether it is essential vs optional for matched occupations,
- transferability across occupations.

Output should say things like:

> “Azure appears in 28% of matched cloud/support postings in region X, up 7 pp YoY, across 64 employers.”

not simply:

> “Azure is a good skill.”

### Language insight to calculate

Language recommendation should combine:

- language explicitly required in matched job ads,
- CEFR level where job ads state it,
- occupation + region,
- salary/demand differential for multilingual roles where measurable,
- user’s current level and estimated learning effort.

The country’s official/main language is only a starting point. For many occupations, English, German, French, Dutch, etc. can have very different labour-market value even within the same country.

---

## 6. How professional systems derive insights

### Cedefop
Separates **demand**, **supply**, and **imbalances** and validates cross-country forecast models with national experts. Its Skills-OVATE layer adds near-real-time online-job-ad demand and explicitly warns that OJA evidence must complement surveys/official statistics.

### LinkedIn Economic Graph
Defines a skill gap as a local, time-specific difference between skill supply and employer demand; employer demand includes skills in postings and skills employers actually hire for.

### Lightcast
Collects job postings from employer sites and job boards, deduplicates them, normalises titles/occupations/locations and extracts skills, salary, experience, credentials and other fields. Crucially, it also states that postings are not identical to vacancies.

### OECD / Eurostat well-being frameworks
Do not equate GDP with quality of life. They use multiple domains and distinguish objective conditions from subjective experience.

### Composite ranking practice
OECD/JRC guidance warns that indicator selection, normalisation, weights and aggregation change rankings. Sensitivity/uncertainty analysis is necessary if a composite ranking is used.

---

## 7. Recommended AUGUR product architecture

### Layer A — Country & Region Reality

Purpose: **“How is this place doing?”**

Each domain should show:

- current level,
- trend,
- peer percentile,
- forecast where official,
- source quality,
- freshness,
- geographic level,
- confidence/uncertainty,
- key drivers.

Do not generate a universal overall score.

### Layer B — Labour Market Intelligence

Purpose: **“Where are my occupation and skills valuable?”**

For the selected occupation/profile:

- occupation match,
- vacancy/demand level,
- shortage/surplus,
- current and future demand,
- top requested skills,
- rising/falling skills,
- salary range/reference,
- required languages,
- regional hotspots,
- employer diversity,
- evidence quality.

### Layer C — Personal Fit

Purpose: **“How viable is this place for me?”**

Use:

- legal access,
- language gap,
- skill gap,
- occupation demand,
- expected income,
- tax/net-income scenario,
- housing affordability,
- household needs,
- location preferences,
- remote-work portability,
- user-selected life priorities.

### Personal ranking

Only create a ranking after the user sets priorities/weights.

Show:

- why each place ranks where it does,
- trade-offs,
- sensitivity to weights,
- missing-data penalties,
- whether top choices remain top under plausible changes in assumptions.

A label such as **Robust fit / Preference-sensitive / Evidence-limited** is more useful than a false-precision score.

---

## 8. UI audit from automated screenshots

AUGUR CI now captures reproducible screenshots for Overview, Indicators, Dimension Detail, Outlook, Compare and Profile at 1920×900, plus full-page secondary views.

### Overview

Current strengths:
- strong visual hierarchy,
- separates map / dimensions / personal readiness / outlook / compare,
- evidence provenance is much safer after recent cleanup.

Next mockup:
- replace “dashboard of panels” with a **Country Radar**:
  - headline strengths/pressures,
  - domain cards with level + trend + peer position,
  - recent changes,
  - evidence age/quality,
  - local/regional toggle.

### Indicators

Current problem:
- technically correct but card-by-card layout wastes space and makes systematic comparison hard.

Next mockup: **Evidence Explorer**
- dense sortable table/list,
- sparkline per indicator,
- latest level,
- 1/3/5y movement,
- peer percentile,
- source and freshness,
- evidence-quality badge,
- filter by dimension/source/quality,
- provenance drawer.

### Dimension Detail

Current problem:
- repeats much of Indicators and does not explain why the dimension conclusion was reached.

Next mockup:
- top synthesis with drivers,
- “supporting / opposing / contextual” evidence lanes,
- correlation/duplicate-warning,
- local-vs-peer comparison,
- confidence explanation.

### Outlook

Current problem:
- horizon cards are easy to read but the page becomes empty when official forecasts are unavailable and it does not communicate historical forecast reliability.

Next mockup: **Future Paths**
- official forecast time-series first,
- forecast-vintage and revision history,
- empirical historical forecast error / fan only when available,
- AUGUR scenarios visually separated below,
- assumptions and calibration state visible.

### Compare

Current problem:
- current table is neutral and correct but does not help the user see trade-offs quickly.

Next mockup: **Decision Matrix**
- grouped domain rows,
- absolute value + peer percentile + trend,
- highlight differences, not “winner” decoration,
- toggle Objective / My priorities,
- sensitivity/robustness panel,
- missing evidence shown explicitly.

### Profile

Current page is now visually coherent. The remaining product problem is that the form is still the first thing the user encounters.

Next mockup: **My Fit**
- compact profile summary/edit affordance,
- top actionable gaps,
- country fit modules,
- “what improves my options?” actions,
- skills/languages recommendation block,
- TTV only after dependencies are evidence-ready.

### New page — Skills & Languages

This is essential for AUGUR’s actual purpose.

Suggested layout:
- occupation selector / matched occupation,
- country/region filter,
- **Skills in demand**: demand share, YoY change, employer count,
- **My gaps**: required skills not declared,
- **Portable skills**: skills demanded in many countries,
- **Languages**: posting demand, level requirements, learning effort,
- **Future demand**: Cedefop forecast,
- evidence-quality / data-window controls.

---

## 9. Implementation priority

### P0 — inference correctness before adding a ranking
1. Rename/split trend “confidence” into evidence depth vs trend certainty.
2. Introduce indicator-specific material-change thresholds.
3. Add peer percentile/reference group.
4. Detect correlated/duplicate indicators before dimension synthesis.
5. Add source freshness/quality metadata directly to conclusions.
6. Keep AUGUR scenarios experimental until calibrated/backtested.

### P1 — directly increase decision usefulness

**P1 implementation status: COMPLETE WITHIN PUBLIC-DATA BOUNDARY**

AUGUR now implements every P1 evidence layer that can be sourced reproducibly from the verified public-data paths currently available. Detailed Skills-OVATE skill-demand and job-ad language shares remain explicitly source-access-gated behind Eurostat microdata access; this is an external evidence-access boundary, not silently missing implementation.

Current implementation status:

1. **Cedefop OJA evidence — PARTIAL / ACTIVE**
   - Cedefop OJA occupational-imbalance 2026-05 integrated as EU27-level exploratory ISCO-4 context;
   - 308 occupations loaded;
   - exact ISCO-4 only;
   - does not substitute Skills-OVATE skill-demand shares.
2. **Cedefop Skills Forecast — ACCESS-GATED**
   - 2026 release verified;
   - projections to 2035 by country, sector, occupation and education;
   - full spreadsheet requires Cedefop request/registration and cannot be redistributed;
   - AUGUR must not scrape the visualisation or pretend the gated dataset is reproducibly available.
3. **Cedefop STAS — ACTIVE**
   - August 2026 release integrated;
   - 282 rows for ESP/IRL/PRT;
   - periods 2026–2027;
   - ISCO 2-digit preferred, ISCO 1-digit fallback;
   - context-only for CareerFit.
4. **Regional/NUTS geography — ACTIVE / EXPANDING**
   - quarterly regional JVS `jvs_q_isco_r21` inspected but does not cover ES/PT/IE NUTS2 regions in 2026-Q2, so AUGUR does not infer regional occupation vacancy pressure from it;
   - Eurostat NUTS2 employment and unemployment rates are active for ES/PT/IE;
   - 36 NUTS2 regions loaded, including Galicia and Principado de Asturias;
   - regional sector-employment ingestion via `lfst_r_lfe2en2` is implemented to describe economic structure by NACE;
   - regional sector composition remains context, not occupation-specific vacancy evidence.
5. **language requirements extracted from OJAs — SOURCE-ACCESS-GATED**
   - Skills-OVATE exposes language-related OJA analytics interactively, but detailed data access is organised through Eurostat's Microdata access portal;
   - AUGUR does not scrape Tableau or infer language-demand shares from ESCO;
   - the public Cedefop 2026 OJA imbalance CSV contains only a combined EU27 occupation score, so its non-native-language component cannot be decomposed into a country language-demand percentage;
   - CareerFit now returns a structured `source_access_gated` state rather than a null/zero placeholder.
6. **occupation/skill demand trend — PARTIAL / ACTIVE**
   - occupation short-term trend is active through Cedefop STAS 2026–2027 employment outlook, exposed as contextual occupation trend by ISCO 2-digit with ISCO 1-digit fallback;
   - STAS growth direction is explicitly labelled as employment outlook, not OJA demand growth or statistical significance;
   - detailed skill-demand shares and skill time series remain source-access-gated behind Skills-OVATE / Eurostat microdata;
   - ESCO relationships remain taxonomy evidence and are never substituted for employer-demand frequency.
7. **housing affordability vs income — ACTIVE / EXPANDING**
   - NUTS2 disposable household income per inhabitant in PPS integrated from `nama_10r_2hhinc`;
   - NUTS2 housing-cost overburden integrated from `ilc_lvho07_r`;
   - overburden is already defined relative to disposable household income (>40% housing-cost threshold), so AUGUR does not derive a redundant synthetic ratio;
   - regional periods remain explicit when income and housing series have different latest years.
8. **healthcare access — ACTIVE / EXPANDING**
   - NUTS2 unmet medical examination needs integrated from `hlth_silc_08_r` where regional reporting exists;
   - NUTS2 available hospital beds per 100,000 integrated from `hlth_rs_bdsrg2`;
   - Portugal currently has no NUTS2 unmet-needs observations in this source, so AUGUR leaves the regional value unavailable rather than copying the national figure;
   - unmet needs and bed capacity remain separate signals and are not combined into a synthetic healthcare score.
9. **environment/air quality — ACTIVE / EXPANDING**
   - observed city PM2.5 is integrated from validated EEA E1a measurements via the official Parquet download API;
   - EEA city names are mapped to Urban Audit/GISCO city codes by normalized exact matching, with only the official "(greater city)" qualifier ignored; ambiguous matches are rejected;
   - annual city PM2.5 requires at least 75% calendar-year coverage per sampling point, uses validated/verified observations only, and averages eligible sampling-point annual means;
   - the 2024 Oviedo live-source validation produced 9.0111 µg/m³ from two eligible hourly sampling points; one daily stream was excluded for insufficient coverage;
   - city PM2.5 is labelled observed monitoring evidence and is not treated as population-weighted exposure or NUTS2 environmental evidence;
   - EEA burden-of-disease data for countries/NUTS/cities is a separate future environmental-health extension, not merged into the concentration signal.
10. **safety and access-to-services — ACTIVE / EXPANDING**
   - NUTS2 household internet access is integrated from Eurostat `isoc_r_iacc_h` as access/connectivity context;
   - NUTS2 air-passenger throughput is integrated from `tran_r_avpa_nm` using passengers carried in thousand passengers, as regional connectivity context rather than a universal quality-of-life score;
   - NUTS3 police-recorded intentional homicide and robbery rates are exposed separately from `crim_gen_reg` in per-100,000 units;
   - NUTS3 crime is never silently copied or aggregated to NUTS2, and categories are not collapsed into a synthetic crime score;
   - live validation confirmed reproducible values for ES120, PT170 and IE061; source periods remain explicit, including Portugal's older latest observation where applicable;
   - cross-country crime comparisons retain explicit caveats for differences in law, reporting behaviour and police-recording practices;
   - a dedicated NUTS3 sync command exists for the local DuckDB store, while the lightweight live smoke probes only a small representative set to avoid unnecessary source load.

Important P1 boundary:
- Skills-OVATE detailed skill-demand shares remain unavailable through a stable reproducible public API/download workflow;
- AUGUR must keep unavailable skill-share, employer-count and language-demand metrics explicitly missing rather than infer them from ESCO or aggregate OJA signals.

### P2 — personal decision engine

Current implementation status:

1. **user preference weights — ACTIVE**
   - explicit 0–5 weights are stored separately as `decision_weight_<dimension>`;
   - legacy boolean priority chips are not silently converted into weights;
   - blank means no explicit weight, zero explicitly excludes a dimension.
2. **transparent dimension normalisation — ACTIVE**
   - interpretable indicators use selected-set utility normalisation on a 0–1 scale;
   - `higher`, `lower` and explicit `target_range` policies use published formulas returned with the API response;
   - contextual indicators are excluded from utility synthesis;
   - semantic constructs from P0.4 collapse duplicate source series before dimension aggregation;
   - normalised utilities are relative to the selected country set and are not absolute country scores.
3. **personalized comparison — ACTIVE**
   - AUGUR produces a 0–100 selected-set preference-fit index only when every positive-weight dimension has comparable utility for every selected country;
   - missing/contextual weighted evidence blocks the index instead of being imputed;
   - the index is relative to the current selected set and explicit weight profile and is never presented as a universal country ranking.
4. **uncertainty/sensitivity analysis — PARTIAL / ACTIVE**
   - joint local ±1 perturbation of all explicit positive weights is active, bounded to the 0–5 weight scale;
   - the engine evaluates the Cartesian local preference neighborhood, including simultaneous weight changes, and reports whether the neighborhood was exhaustive or capped;
   - the current seven-dimension model has at most 2,187 local combinations, below AUGUR's 5,000-scenario safety cap;
   - per-country preference-fit score ranges are exposed;
   - tested rank ranges, first-place scenario counts and a `rank_stable` / `preference_sensitive` label are exposed for the same tested joint neighborhood;
   - the Decision Matrix displays whether the tested neighborhood was exhaustive;
   - this measures preference-weight sensitivity only, not statistical uncertainty in source observations or the probability that a country is best;
   - probabilistic evidence-error propagation remains intentionally unimplemented until a defensible heterogeneous-source uncertainty model exists.
5. **robust/Pareto choices — ACTIVE**
   - Pareto nondominance is calculated on positive-weight, fully comparable dimensions;
   - the UI reports a Pareto candidate set, never a universal “best country”;
   - a country is dominated only if another is no worse on every included dimension and strictly better on at least one.

P2 implementation boundary:
- objective country evidence remains unchanged by preferences;
- any weighted dimension without normalisable comparable evidence becomes an explicit blocker;
- sensitivity ranges are local joint preference-model robustness, not confidence intervals or statistical probability;
- if a future model exceeds the 5,000-scenario safety cap, the response must expose `truncated=true` rather than presenting partial exploration as exhaustive.

### P3 — commercial/live data if needed

**P3 status: CONTRACT READY / PROVIDER NOT CONFIGURED**

- a vendor-neutral `live-postings-v1` evidence contract is implemented;
- CareerFit exposes `provider_not_configured` explicitly rather than treating absent live data as zero demand;
- operability reports live-postings provider status but does not make it a blocker for the verified public-data model;
- provider-specific live evidence remains context-only and cannot change CareerFit/TTV gates without a separate validated methodology;
- Lightcast currently has the strongest semantic fit for enriched occupation/skill analytics, while Coresignal is the most practical self-service pilot candidate;
- Adzuna is suitable for basic live posting/salary context but should not be assumed to provide structured skill-demand analytics through its standard developer API;
- Jooble's documented 500-lifetime-request free quota per country key is not a good basis for repeatable AUGUR analytics;
- no paid provider will be adopted until a controlled pilot demonstrates decision value beyond the existing EURES / Eurostat / Cedefop stack.

Detailed provider evaluation: `docs/LIVE_POSTINGS_PROVIDER_EVALUATION_2026-10-07.md`.

---

## 10. External methodological references

- Eurostat Quality of Life methodology:
  https://ec.europa.eu/eurostat/web/quality-of-life/methodology
- OECD Regional Well-Being:
  https://www.oecd.org/en/data/tools/oecd-regional-well-being.html
- OECD/JRC Handbook on Constructing Composite Indicators:
  https://www.oecd.org/en/publications/handbook-on-constructing-composite-indicators-methodology-and-user-guide_9789264043466-en.html
- Cedefop Skills Forecast:
  https://www.cedefop.europa.eu/en/tools/skills-forecast
- Cedefop Skills intelligence / online job advertisements:
  https://www26.cedefop.europa.eu/en/tools/skills-intelligence/trend-focus/skills-online-job-advertisements
- Eurostat experimental job vacancy by occupation and region:
  https://ec.europa.eu/eurostat/en/web/experimental-statistics/job-vacancy-rate-occupation-region
- European Labour Authority 2025 shortage/surplus dashboard:
  https://www.ela.europa.eu/en/dashboard-ela-quantification-labour-shortages-and-surpluses-europe-2025
- ESCO:
  https://esco.ec.europa.eu/en/classification
- LinkedIn Economic Graph skill-gap methodology:
  https://economicgraph.linkedin.com/blog/Quantifying-skills-gaps-with-the-economic-graph
- Lightcast Job Posting Analytics methodology:
  https://kb.lightcast.io/en/articles/6957446-job-posting-analytics-jpa-methodology
- OECD Taxing Wages methodology:
  https://www.oecd.org/en/publications/taxing-wages-2026_3a5169ef-en/full-report/methodology-and-limitations_f25b8cbc.html
- EEA air-quality data:
  https://www.eea.europa.eu/en/about/contact-us/faqs/where-can-i-access-the-latest-air-quality-data-in-europe/
