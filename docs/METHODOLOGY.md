# AUGUR Methodology

AUGUR separates facts, official forecasts, and modelled scenarios so users can inspect how every conclusion is produced.

## Evidence classes

AUGUR stores each time-series observation with an explicit type:

- `observed` — historical/current source observation.
- `official_forecast` — forecast or projection published by an external official source.
- `augur_projection` — reserved for deterministic AUGUR projections that may be introduced later.
- scenario values — derived alternatives around an official baseline; never stored or presented as official forecasts.

Observed series are the only inputs to current-state snapshots and historical trend calculations.

## Canonical source selection

Multiple sources may provide the same canonical indicator.

For each observed period AUGUR selects one canonical observation using:

1. latest period for current snapshot;
2. source priority;
3. source ID as deterministic tie-breaker.

Historical trend series select one source per period using the same priority rule. Duplicate source observations are not mixed into a single regression point.

## Source quality

AUGUR reports:

- preferred source and period;
- freshest available period;
- period spread between source publication dates;
- number of independent sources;
- disagreement at the latest period shared by at least two sources.

Source disagreement is only calculated at a **common period**. Values from different years are never labelled as source disagreement.

## Trend engine

Historical trend analysis uses observed data only.

Current outputs include:

- 1-year percentage change;
- 3-year percentage change;
- 5-year percentage change;
- linear-regression slope;
- direction;
- confidence based on available historical coverage.

Interpretation depends on the indicator policy:

- `higher`
- `lower`
- `target_range`
- `contextual`

Contextual indicators are not automatically labelled good or bad.

## Target ranges

Target ranges are modelling rules, not claims that an official institution has adopted that exact interval.

The initial inflation range of 1–3% is an AUGUR modelling assumption and must not be described as an official target.

## Dimension synthesis

Signals are grouped into analytical dimensions.

The current dimensions are:

- Prosperity
- Productive capacity
- Housing
- Demography
- Human systems
- Fiscal sustainability
- Strategic resilience

Institutional/geopolitical environment remains a future expansion area.

Dimension synthesis is transparent signal aggregation. AUGUR does **not** generate a universal country score.

## Official outlook

The official outlook view displays only observations marked `official_forecast`.

Current fixed horizons:

- 2030
- 2035
- 2045

Different official sources naturally have different horizons. Missing official coverage is shown as missing rather than extrapolated silently.

## AUGUR scenarios

Scenario names:

- baseline
- improvement
- stress

Baseline equals the official forecast/projection.

Improvement and stress are deterministic AUGUR assumptions around that baseline. They are not official forecasts.

Scenario envelopes widen with horizon:

- 2030: near uncertainty, ×1.0
- 2035: medium uncertainty, ×1.5
- 2045: long uncertainty, ×2.5

Contextual indicators are not directionally altered automatically.

## Comparison

Country comparison aligns canonical current observations by indicator.

It does not:

- rank countries;
- declare a winner;
- create an opaque aggregate score.

Publication periods and preferred source IDs remain visible.

## Personal fit boundary

Personal Fit operates **after** the country evidence layer.

Personal preferences may change whether a country fits a household. They must never alter:

- source observations;
- official forecasts;
- country trends;
- country-level evidence quality.

This boundary keeps descriptive country analysis separate from individual decision support.


## Current Personal Fit methods

### Profile readiness

Profile readiness only reports whether the inputs required by a Personal Fit module are present. It is not a country-fit result.

### LegalFit

LegalFit currently resolves:

- domestic cases;
- EU free-movement framework cases for EU citizens moving to an EU target;
- otherwise, an explicit `country_specific_rules_required` state.

It does not infer visa or residence eligibility where verified country-specific rules are absent.

### LanguageFit

LanguageFit compares declared CEFR levels with target labour-market languages.

The current B2 threshold is an AUGUR professional work-readiness heuristic, not a legal requirement.

When a confident ESCO occupation match and ESCO language-skill metadata are available, LanguageFit also exposes occupation-linked language skills as a separate evidence layer. Essential/optional ESCO relationships are preserved.

ESCO occupation-language relationships do **not** encode a CEFR threshold, so they never convert the B2 heuristic into an official or occupation-specific requirement.

### CareerFit

CareerFit combines:

1. transparent profession-to-broad-occupation classification;
2. EURES shortage/surplus signals for the implemented countries;
3. local ESCO occupation resolution;
4. ESCO essential-skill coverage when a full ESCO dataset is loaded.

ESCO occupation resolution is confidence-gated. Low-confidence candidates are not silently accepted.

Seed ESCO data validates the local pipeline but can never mark skill evidence complete.

AUGUR distinguishes **evidence completeness** from **viability evidence**. A full ESCO dataset can make the occupational evidence complete, but TTV does not treat CareerFit as ready unless the profile also declares complete coverage of the ESCO skills marked essential for that occupation and the implemented EURES signal is supportive (`shortage`).

This is deliberately conservative: ESCO essential skills are normally required across employers and contexts, but a supportive shortage signal plus declared skill coverage is still not a guarantee of employment.

### FinancialFit

For portable income, FinancialFit compares origin and target household price-level indices and reports relative purchasing-power change.

It does not assume that current income survives relocation unless the profile explicitly states that remote work is viable.

For local employment, AUGUR now exposes two separate official evidence layers:

- Eurostat SES 2022 mean gross monthly earnings for the matched broad ISCO-08 occupation group;
- Eurostat annual net earnings for the national standard case `P1_NCH_AW100` (single person without children earning 100% of the average wage).

These layers are deliberately **not merged into an occupation-specific net salary estimate**. The national net benchmark is not occupation-specific and the SES occupational reference is gross.

Local-employment FinancialFit therefore remains partial and exposes structured blockers:

- occupation-specific net income;
- household budget;
- transition costs.

Household Budget Survey and national-accounts COICOP evidence may provide useful national context, but AUGUR does not treat those aggregates as an individual household budget.

This conservative boundary also means that liquid savings are not yet converted into a transition runway until a defensible transition-cost model exists.

### TTV

TTV is a dependency graph, not an aggregate score.

Current viability dependencies are:

- LegalFit
- LanguageFit
- CareerFit
- FinancialFit

A separate temporal-evidence engine now evaluates candidate timing evidence for:

- legal access;
- language progression;
- essential-skill gaps;
- financial transition;
- employment transition.

The temporal engine may expose a **candidate range for validation**, but AUGUR does not publish that range as a TTV estimate while `TEMPORAL_MODEL_VERSION` remains unset.

Current temporal evidence includes:

- zero additional legal delay for domestic cases and EU free-movement work rights;
- Cambridge English guided-learning-hour ranges for progression to AUGUR's B2 heuristic, converted to calendar weeks only when the user supplies weekly study intensity;
- zero skill-training delay only when declared essential ESCO skill coverage is already complete;
- zero employment-transition delay for preserved remote income;
- an experimental Eurostat country-level unemployment-to-employment transition baseline for local employment, using the profile age class when a matching Eurostat group is available and falling back explicitly to ages 15–74 otherwise.

The Eurostat employment baseline is not occupation-specific and uses a constant quarterly-hazard assumption only to produce a validation range. It is not an individual job-offer forecast. Profiles outside the Eurostat 15–74 transition population are not extrapolated.

Candidate stage durations are currently composed with `parallel_max`: stages that can progress concurrently are not blindly summed. This composition remains experimental and is one of the items that must be validated before a temporal model can be versioned.

Local-employment cases remain blocked from a complete calendar range while FinancialFit lacks a validated net-income / tax / household-budget transition model.

AUGUR therefore distinguishes:

1. dependency readiness;
2. temporal evidence readiness;
3. candidate temporal range;
4. published TTV estimate.

Only the fourth requires an explicitly versioned and validated temporal model.
