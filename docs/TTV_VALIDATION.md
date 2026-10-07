# AUGUR TTV Temporal Model Validation

AUGUR does not publish a Time-to-Viability duration merely because candidate timing evidence exists.

The temporal evidence engine and the published TTV model are separate layers.

## Current state

- Temporal evidence engine: `ttv-temporal-evidence-v1`
- Published temporal model: **not versioned**
- `TEMPORAL_MODEL_VERSION`: `None`
- Candidate ranges may be displayed for validation.
- Candidate ranges are not AUGUR TTV estimates.

## Validation rule

The temporal model can only be versioned when every validation gate is either `supported` or explicitly `scope_bounded`, and no unresolved blocker remains. A scope-bounded gate means AUGUR excludes that case class rather than inventing an unsupported duration.

The current gate policy is exposed by:

```text
GET /api/operability
→ ttv_temporal_validation
```

and by:

```powershell
.\check-operability.ps1
```

## Gates

| Gate | Current state | Meaning |
| --- | --- | --- |
| legal_domestic_eu_timing | supported | Domestic and EU free-movement work-right timing has an explicit evidence path. |
| language_guided_hours | supported | CEFR progression uses published guided-learning-hour ranges. |
| language_calendar_intensity | supported | Calendar conversion requires explicit user study hours/week. |
| skill_gap_duration | scope_bounded | TTV v1 requires complete declared essential-skill coverage; cases with a skill gap are outside estimation scope. |
| remote_income_transition | supported | Preserved remote income does not require a job-search transition stage. |
| local_employment_transition | scope_bounded | TTV v1 excludes local job-search timing rather than converting country transition probabilities into an individual duration. |
| local_financial_transition | scope_bounded | TTV v1 requires preserved portable income; local financial-transition timing remains outside scope. |
| composition_dependency_graph | supported | Within the bounded v1 scope, legal/language/skills preparation can overlap and the employment/financial stages are zero-duration, yielding an explicit critical path. |
| external_calibration | missing | Candidate ranges have not yet been validated on a frozen representative holdout of observed viability outcomes. |

## What does not qualify as validation

The following are useful evidence, but are insufficient on their own to activate a published TTV model:

- a green CI run;
- complete profile inputs;
- a full ESCO import;
- supportive EURES shortage evidence;
- complete declared essential-skill coverage;
- Eurostat SES gross earnings;
- Eurostat national average-worker net earnings;
- a candidate temporal range.

## Activation condition

The model should only receive a non-null `TEMPORAL_MODEL_VERSION` when:

1. every gate is `supported`;
2. backend tests cover the accepted assumptions;
3. the methodology documentation names the model version and evidence basis;
4. candidate-range behaviour is tested for both remote-income and local-employment cases;
5. the resulting duration remains inspectable as stage evidence rather than an opaque score.

Until then, withholding a TTV duration is the intended product behaviour.


## Candidate composition

The candidate temporal engine no longer assumes that every stage progresses fully in parallel.

Current bounded v1 dependency structure:

1. legal, language and skills preparation may progress in parallel;
2. v1 requires complete essential-skill coverage, so the skills duration is zero for in-scope cases;
3. v1 requires preserved portable remote income, so employment-search and local-financial transition durations are zero;
4. the remaining candidate range is therefore the critical path across applicable preparation stages.

The implementation still uses the general formula:

`max(legal, language, skills) + employment + financial`

but in-scope v1 cases have zero employment and financial transition stages. The composition is therefore supported as structural scope logic. This does **not** satisfy external calibration and does not activate a published TTV estimate on its own.


## Local-employment transition boundary

The current employment timing stage uses Eurostat's experimental unemployment-to-employment transition probability.

AUGUR has also reviewed Eurostat occupation-level demand evidence:

- job vacancy statistics by occupation;
- experimental job-vacancy rate by occupation and region;
- online job-advertisement rate by occupation.

These sources add occupational demand context, but they do **not** report an occupation-specific probability or elapsed time from unemployment to employment.

AUGUR therefore does not convert vacancy rates or advertisement rates into weeks-to-employment.

The `local_employment_transition` path remains implemented as exploratory evidence, but it is **outside TTV v1 estimation scope** until one of the following exists:

1. direct occupation-specific transition-duration/probability evidence suitable for the target population; or
2. an externally calibrated model that demonstrates how occupational demand evidence can be converted into elapsed transition time.

Until then, occupation-level vacancy evidence may improve CareerFit, but it must remain separate from the TTV duration model.


## External calibration infrastructure

AUGUR now includes a local-first calibration lifecycle rather than relying on manual CSV entry alone.

For an eligible bounded TTV v1 case, My Fit can:

1. start an explicit opt-in development observation;
2. freeze the candidate range and model context before the outcome is known;
3. keep the active observation separate from completed calibration cases;
4. record a user-confirmed documented B2-or-better outcome;
5. calculate observed elapsed weeks from the stored start/outcome timestamps;
6. create a `sample_role=development` calibration case;
7. cancel an observation without creating calibration evidence.

CSV import remains available as a compatibility/development path.

The calibration store records only the minimum fields required to evaluate the candidate model:

- anonymous `case_id`;
- target country;
- employment mode;
- temporal evidence engine version;
- composition version;
- candidate range minimum and maximum;
- observed weeks to viability;
- frozen start/outcome definition versions;
- optional stage timings;
- bounded non-sensitive model context: scope ID, starting/target CEFR, weekly study intensity and guided-hour range.

It deliberately does **not** store or exchange the full personal profile.

The current descriptive diagnostics include:

- sample and country counts;
- candidate-interval coverage;
- mean and median interval width;
- mean absolute midpoint error;
- mean signed midpoint error;
- count/direction of misses below or above the interval;
- mean miss distance outside the interval;
- the same diagnostics by sample role and available stage timing;
- represented starting CEFR levels and study-intensity cohorts.

AUGUR also supports a versioned `ttv-development-exchange-v1` package for moving development cases between local installations. The package excludes direct identifiers, full profiles, free-text histories, local provenance labels and exact local import/observation timestamps. Imported exchange cases remain development evidence and cannot be promoted retrospectively into holdout evidence.

These diagnostics and exchange mechanisms do not constitute validation on their own.

The `external_calibration` gate remains `missing` until AUGUR has:

1. a representative observed sample inside the frozen TTV v1 scope;
2. a frozen calibration protocol version;
3. acceptance criteria defined before evaluating the final holdout sample;
4. a frozen holdout not used for model design/tuning;
5. evidence that the model performs acceptably on that holdout;
6. documented cohort coverage and limitations.

The local calibration workflow is therefore validation infrastructure, not a shortcut to activating `TEMPORAL_MODEL_VERSION`.


## Local-financial transition boundary

AUGUR has reviewed the available Eurostat household-spending evidence for a possible local financial transition model.

Relevant sources include:

- Household Budget Surveys (HBS);
- household final consumption expenditure by COICOP;
- housing-cost burden indicators;
- purchasing-power and price-level statistics.

These sources are useful for national or household-group context, but they are not an individual relocation budget and they do not directly encode:

- the target household's actual rent or mortgage;
- deposit and agency costs;
- moving costs;
- utility setup costs;
- transport changes;
- household-specific recurring expenditure;
- monthly savings capacity;
- the amount of liquid savings the user is willing to deploy;
- elapsed time required to accumulate any shortfall.

Eurostat also notes that Household Budget Survey comparability is not fully harmonised across countries.

AUGUR therefore does not turn national household expenditure averages into an individual transition-cost estimate.

The `local_financial_transition` path remains outside TTV v1 estimation scope until AUGUR has a defensible household-level transition-cost input/evidence model. Any future model must distinguish:

1. official contextual price/expenditure evidence;
2. user-declared household assumptions;
3. actual transition costs;
4. savings/runway mechanics;
5. uncertainty in the resulting duration.

Until then, national expenditure evidence may enrich FinancialFit context, but it must not unlock a TTV duration.


## TTV v1 estimation scope

The first versionable TTV model is deliberately narrower than the full dependency graph.

An in-scope v1 case requires:

- preserved portable remote income;
- complete declared essential-skill coverage and supportive CareerFit viability evidence;
- domestic or EU free-movement legal timing supported by the current LegalFit implementation;
- either B2-or-better target-language readiness, or a declared CEFR level plus explicit weekly study intensity so guided hours can be converted to calendar weeks.

Out of scope for v1:

- local-employment job-search timing;
- cases with unresolved essential-skill gaps;
- local financial-transition / relocation-budget accumulation timing;
- legal regimes whose timing has not been verified by the current LegalFit evidence path.

Scope exclusion is not equivalent to a zero duration. AUGUR withholds the candidate range for out-of-scope cases.

With this bounded scope, the only remaining temporal-model validation blocker is external calibration against observed outcomes.
