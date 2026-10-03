# AUGUR TTV Calibration Protocol — Draft

Status: **draft / not approved**

## Current executable blockers

AUGUR currently reports these calibration-protocol blockers through `/api/operability` and `check-operability.ps1`:

- protocol version not approved;
- start-event definition not frozen;
- viability-outcome definition not frozen;
- inclusion/exclusion rules not frozen;
- acceptance criteria not frozen.

Until every blocker is cleared, holdout collection remains disabled by code.

This document defines the data and evaluation process required before AUGUR can claim that a Time-to-Viability model has been externally calibrated.

It does **not** activate `TEMPORAL_MODEL_VERSION`.

## 1. Purpose

The calibration dataset exists to answer two separate questions:

1. Are the candidate TTV intervals consistent with observed Time-to-Viability outcomes?
2. Are the individual stage assumptions and the `critical_path_v1` composition consistent with observed stage durations?

AUGUR must not tune the model on the final evaluation sample and then report performance on that same sample.

## 2. Observed outcome

An observed case requires an anonymised elapsed duration expressed in weeks.

`observed_weeks` is the elapsed time between:

- the pre-declared start event for the case; and
- the first date on which the case satisfies the agreed observed viability outcome.

The exact start-event and viability-outcome definitions must be frozen before a calibration protocol can move from draft to approved.

Until those definitions are approved, imported cases remain exploratory.

## 3. Minimum case fields

Required:

- anonymous `case_id`;
- target `country_iso3`;
- `employment_mode`: `remote` or `local`;
- temporal `engine_version`;
- `composition` version;
- candidate minimum weeks;
- candidate maximum weeks;
- observed weeks.

Calibration-control metadata:

- `sample_role`: `development` or `holdout` (defaults to `development`);
- `start_event_definition_version`;
- `viability_outcome_definition_version`.

Optional:

- source/provenance label;
- observation date;
- stage-level timings.

### Sample role and protocol lock

Development cases may be collected while the protocol is still a draft. They remain exploratory.

Holdout cases are different. AUGUR rejects a `sample_role=holdout` import while `CALIBRATION_PROTOCOL_VERSION` is unset.

A holdout case will also require:

- a frozen start-event definition version;
- a frozen viability-outcome definition version.

This lock is enforced by the calibration importer, not only by documentation.

The calibration store does not contain the full personal profile.

## 4. Stage-level observations

When available, the following stages may be supplied:

- legal;
- language;
- skills;
- employment;
- financial.

Each included stage must contain:

- candidate minimum weeks;
- candidate maximum weeks;
- observed weeks.

Stage-level data are needed to distinguish:

- a stage-duration error;
- a dependency/composition error;
- an overall TTV interval error.

## 5. Cohorts

Results must be inspectable at least by:

- target country;
- remote vs local employment mode;
- temporal engine version;
- composition version.

Additional cohorts may be introduced only when they are defined before evaluating the final holdout sample.

Small cohort results must not be presented as stable estimates.

## 6. Development and holdout separation

Calibration work must distinguish:

### Design / development sample

May be used to:

- inspect failure modes;
- adjust stage definitions;
- revise evidence sources;
- revise dependency sequencing;
- revise model assumptions.

### Final holdout sample

Must not be used to design or tune the model.

The holdout evaluation is only meaningful after:

- the candidate temporal model is frozen;
- the calibration outcome definition is frozen;
- inclusion/exclusion rules are frozen;
- acceptance metrics and thresholds are frozen.

## 7. Current descriptive metrics

AUGUR currently reports:

- case count;
- country count;
- employment modes;
- engine versions;
- composition versions;
- candidate-interval coverage;
- mean absolute midpoint error;
- mean signed midpoint error;
- the same interval/error metrics for each stage when stage timings are available.

These metrics are descriptive.

No current metric has an approved pass/fail threshold.

## 8. Required future acceptance criteria

Before a final holdout evaluation, AUGUR must define:

- minimum total sample size;
- minimum useful sample size for relevant cohorts;
- target interval coverage;
- acceptable interval width / sharpness;
- acceptable midpoint error;
- acceptable systematic under- or over-estimation;
- handling of censored or incomplete observations;
- handling of model/version changes during collection.

Those thresholds must be written before the final holdout is evaluated.

## 9. Versioning rule

Every calibration case is tied to:

- `engine_version`;
- `composition`.

A case generated against one model version must not be silently treated as calibration evidence for a different version.

A future approved calibration protocol should also receive its own immutable protocol version.

## 10. Privacy boundary

The local calibration store is intentionally minimal.

Do not store:

- names;
- email addresses;
- addresses;
- free-text personal histories;
- full PersonalProfile payloads;
- unnecessary demographic or health information.

Provenance labels should identify a source category or study, not a person.

## 11. Gate transition

The `external_calibration` TTV validation gate remains `missing` while this protocol is draft.

Moving the gate to `supported` requires all of the following:

1. an approved protocol version;
2. a representative observed dataset;
3. a frozen model version;
4. a frozen holdout;
5. pre-declared acceptance criteria;
6. successful holdout evaluation;
7. documented limitations and cohort coverage.

Infrastructure, sample count, or green CI alone do not satisfy the gate.


## 12. Development-case collection workflow

AUGUR includes an empty CSV template:

`docs/TTV_CALIBRATION_TEMPLATE.csv`

Use it only for observed cases. Do not insert synthetic or illustrative rows into the calibration store.

While this protocol remains draft:

- use `sample_role=development`;
- leave holdout collection disabled;
- record the temporal `engine_version` and `composition` that generated the candidate interval;
- add stage-level timings only when the observed stage boundaries are genuinely known;
- use source labels that identify the evidence source category, not a person.

Import locally with:

```powershell
.\import-ttv-calibration.ps1 -Path ".\path\to\observed-development-cases.csv"
```

Imported development cases may be inspected descriptively, but they do not satisfy the external-calibration gate.
