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

The temporal model can only be versioned when every validation gate is in the `supported` state.

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
| skill_gap_duration | missing | No accepted training-duration model exists for missing essential ESCO skills. |
| remote_income_transition | supported | Preserved remote income does not require a job-search transition stage. |
| local_employment_transition | experimental | Country-level unemployment-to-employment transitions are not occupation-specific. |
| local_financial_transition | missing | Occupation-specific net income, household budget and transition costs are incomplete. |
| composition_dependency_graph | experimental | The stage dependency graph is explicit, but its sequencing assumptions have not been externally calibrated. |
| external_calibration | missing | Candidate ranges have not been calibrated against observed relocation outcomes. |

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

Current experimental dependency structure:

1. legal, language and skills preparation may progress in parallel;
2. employment transition follows preparation;
3. financial transition follows employment.

The candidate range therefore follows a critical-path composition:

`max(legal, language, skills) + employment + financial`

This is more explicit than the previous `parallel_max` rule, but it remains an experimental modelling assumption until externally calibrated. It does not activate a published TTV estimate.
