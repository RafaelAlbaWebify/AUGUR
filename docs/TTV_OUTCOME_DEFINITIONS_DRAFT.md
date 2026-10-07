# AUGUR TTV Observed Outcome Definitions — v1 bounded scope

Status: **definitions frozen / calibration acceptance pending**

Frozen definition IDs:

- start event: `ttv-start-active-language-transition-v1`;
- viability outcome: `ttv-outcome-b2-remote-viability-v1`;
- inclusion/exclusion rules: `ttv-inclusion-remote-scope-v1`.

These definitions apply only to the bounded TTV v1 estimation scope. They do **not** approve the calibration protocol and they do **not** validate the temporal model.

## 1. Scope

A calibration case is eligible for the future TTV v1 holdout only when all of the following are true at the start event:

- the target country has already been chosen;
- the case uses preserved portable remote income;
- LegalFit is already satisfied through the currently supported domestic/EU-free-movement path;
- CareerFit has complete declared essential-skill coverage and supportive viability evidence;
- there is no unresolved local-employment transition;
- there is no unresolved local-financial transition;
- the only non-zero temporal preparation stage may be language progression.

Local-employment cases, unresolved essential-skill gaps and local financial-transition cases may still be retained as development evidence, but they cannot validate TTV v1.

## 2. Frozen start event

### `ttv-start-active-language-transition-v1`

For a non-zero language-transition case, the clock starts on the first calendar date after the target country has been selected when the person begins an intentional CEFR progression plan toward the model target level and the weekly study intensity used by the candidate model is recorded.

The start record must include:

- target country;
- starting CEFR level used by the candidate model;
- planned study hours per week used by the candidate model;
- confirmation that legal, skill and portable-income scope conditions are already satisfied.

Passive browsing, a general intention to relocate, or language study that predates selection of the target country does not by itself start the clock.

Cases that are already language-ready at baseline have a zero-duration language stage. They may be retained as controls, but they do not provide evidence about language-duration calibration.

## 3. Frozen viability outcome

### `ttv-outcome-b2-remote-viability-v1`

The observed outcome occurs on the first calendar date when:

1. the target-language criterion used by TTV v1 is evidenced at B2 or better through a CEFR-aligned assessment or other documented CEFR result; and
2. the legal, essential-skill and preserved-portable-income conditions that made the case eligible remain satisfied.

The outcome is therefore a bounded **remote-transition viability** event. It is not:

- the date of physical relocation;
- the date of first local employment;
- a prediction of immigration-processing time outside the supported legal scope;
- a household-relocation budget completion date.

## 4. Inclusion/exclusion rules

### `ttv-inclusion-remote-scope-v1`

Include a future holdout case only if:

- employment mode is `remote`;
- engine version is `ttv-temporal-evidence-v1`;
- composition is `critical_path_v1`;
- the candidate range was generated before the observed outcome;
- baseline legal, skill and portable-income scope conditions were satisfied and recorded;
- the baseline language level and weekly study intensity used by the model were recorded;
- the observed outcome date can be supported without synthetic precision.

Exclude from the v1 holdout:

- local-employment transitions;
- unresolved essential-skill gaps at baseline;
- local-financial-transition timing;
- unsupported legal regimes;
- cases where the target country was selected only after the measured language transition had already begun;
- cases where the portable-income condition ceased to hold before the viability outcome;
- cases whose start or outcome date has to be guessed or reconstructed to artificial precision.

If an in-scope case becomes impossible to observe because follow-up ends before the outcome, it must not be silently treated as a completed case. Censoring rules remain part of the still-pending acceptance/evaluation protocol.

## 5. Stage boundaries

Within the bounded v1 scope:

- legal: zero-duration supported prerequisite;
- skills: zero-duration supported prerequisite;
- employment: zero-duration because preserved remote income is required;
- financial: zero-duration because preserved portable income is required;
- language: zero if already work-ready; otherwise the only potentially non-zero stage.

The general `critical_path_v1` implementation remains:

`max(legal, language, skills) + employment + financial`

but the bounded scope makes the non-language stages zero for holdout-eligible v1 cases.

## 6. What remains unfrozen

The following are intentionally still unresolved:

- calibration protocol version;
- numerical acceptance criteria;
- minimum development and holdout sample sizes;
- treatment of censored observations in final scoring;
- final holdout pass/fail thresholds.

These must be frozen **before** the final holdout is evaluated.

## 7. Calibration boundary

Development cases may be collected under these frozen observational definitions.

They remain exploratory and may be used to understand interval coverage, width, midpoint error and failure modes.

No development result, green CI run, or non-zero case count activates TTV. External calibration remains the sole temporal-model validation blocker until a pre-declared holdout protocol is frozen and passed.
