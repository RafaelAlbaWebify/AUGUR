# AUGUR TTV Calibration Protocol — Draft

Status: **definitions frozen / acceptance criteria pending / protocol not approved**

## Current executable blockers

AUGUR currently reports these remaining calibration-protocol blockers through `/api/operability` and `check-operability.ps1`:

- protocol version not approved;
- acceptance criteria not frozen.

The following definitions are now frozen for the bounded remote-only TTV v1 scope:

- start event: `ttv-start-active-language-transition-v1`;
- viability outcome: `ttv-outcome-b2-remote-viability-v1`;
- inclusion/exclusion rules: `ttv-inclusion-remote-scope-v1`.

Until every blocker is cleared, holdout collection remains disabled by code.

The frozen bounded-scope observational definitions are tracked separately in:

`docs/TTV_OUTCOME_DEFINITIONS_DRAFT.md`

The historical filename is retained for compatibility, but the document now contains versioned v1 definitions. Those definitions clear the start-event, outcome and inclusion/exclusion readiness requirements; they do not approve the protocol or clear external calibration.

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

The bounded v1 start-event and viability-outcome definitions are frozen. Imported development cases remain exploratory until acceptance criteria and the final protocol version are frozen.

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

### Calibration context fields

For the bounded language-transition v1 scope, AUGUR may store and exchange only the following non-sensitive calibration covariates:

- `scope_id`;
- starting CEFR level;
- target CEFR level;
- weekly study hours used by the frozen candidate model;
- guided-learning-hour minimum and maximum used by the candidate model.

These fields are required for cohort analysis because elapsed language progression cannot be interpreted responsibly without its starting level and study intensity.

They are **not** a copy of the personal profile. Development exchange packages continue to exclude:

- age;
- profession;
- skills list;
- citizenships;
- income or savings;
- household information;
- names, email addresses or postal addresses;
- free-text personal history;
- exact local provenance labels and local import timestamps.

AUGUR reports the represented CEFR starting levels and study-hour cohorts in calibration diagnostics so sample concentration is visible before any holdout criteria are frozen.

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

### Why width and miss distance matter

Coverage alone is not sufficient. A very wide interval can achieve high coverage while being too vague to support a decision.

AUGUR therefore reports interval width alongside coverage and records the distance from the nearest interval boundary when an observation misses the range.

These diagnostics are descriptive until acceptance thresholds are frozen. They are intended to let the development sample expose the trade-off between:

- empirical coverage;
- interval sharpness;
- midpoint error;
- systematic early/late bias;
- severity and direction of misses.

## 8. Required future acceptance criteria

Before a final holdout evaluation, AUGUR must still define and freeze:

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


## 13. In-product opt-in observation workflow

AUGUR can now collect bounded TTV v1 **development** observations directly from My Fit without requiring CSV entry.

The workflow is deliberately opt-in and local:

1. AUGUR checks that the current TTV candidate is inside `ttv-estimation-scope-v1`;
2. the user explicitly starts a calibration observation;
3. AUGUR stores the frozen candidate range, engine/composition versions, start timestamp and language baseline in the local SQLite datastore;
4. an active observation remains separate from the calibration case store;
5. when the user has a documented B2-or-better result, the user explicitly records the observed outcome;
6. AUGUR calculates elapsed weeks from the stored start timestamp and writes a `sample_role=development` calibration case;
7. cancelling an observation creates no calibration case.

The product does not automatically infer that B2 has been achieved from profile edits, elapsed time or another heuristic.

This workflow reduces manual data-entry error and preserves the pre-outcome candidate range, but it does **not** constitute external validation. Development cases remain exploratory and cannot be promoted to holdout cases retrospectively.

Holdout collection remains disabled until:

- the calibration protocol receives an immutable version;
- acceptance criteria are frozen before holdout evaluation.

The local observation workflow stores only bounded calibration metadata; it does not duplicate the full personal profile in the calibration datastore.


## 14. Development exchange between installations

AUGUR exposes a versioned `ttv-development-exchange-v1` JSON package for moving development evidence between local installations.

The package contains calibration fields, stage timings and the bounded non-sensitive calibration context only.

It deliberately omits:

- the full profile;
- local source labels;
- exact observation/import timestamps;
- all direct personal identifiers.

Imported cases remain `sample_role=development`. The exchange importer rejects attempts to transport holdout cases through the development format.

This mechanism is intended to make a future multi-installation development sample possible while preserving AUGUR's local-first privacy boundary. It does not itself make the sample representative and it does not clear the `external_calibration` gate.
