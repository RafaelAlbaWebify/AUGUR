# AUGUR TTV Observed Outcome Definitions — Draft

Status: **draft / not versioned**

This document translates the current TTV dependency graph into observable calibration events.

It does **not** define an approved start-event version or viability-outcome version.

## 1. Why this exists

A calibration interval is meaningless unless every observed case measures elapsed time from the same kind of start event to the same kind of viability outcome.

AUGUR currently models these temporal stages:

- legal;
- language;
- skills;
- employment;
- financial.

The definitions below are candidate observational boundaries for those stages.

## 2. Candidate start event

### Candidate: active-transition start

The clock would start on the first calendar date when the person begins an intentional transition attempt toward the target country and at least one unresolved TTV stage becomes actively pursued.

Examples of an observable start action include:

- beginning a required language-learning plan;
- beginning training for a required skill gap;
- submitting a required legal/work-right application;
- beginning a target-country local job search;
- beginning a defined financial accumulation/transition plan.

### Why this is not frozen yet

Open questions:

- whether merely deciding to relocate counts;
- whether passive job browsing counts as active job search;
- how to treat preparation that began before the target country was chosen;
- how to treat a stage already underway before the AUGUR assessment;
- whether the earliest active stage or a formal recorded plan date should control the clock.

Until these rules are resolved, `CALIBRATION_START_EVENT_DEFINITION_VERSION` remains unset.

## 3. Candidate viability outcome

### Candidate: simultaneous dependency viability

The observed outcome would occur on the first date when every dependency required by the case is simultaneously satisfied.

Current dependency interpretation:

### Legal

Satisfied when the person has the legal ability required by the case to live/work in the target country, or when AUGUR's implemented framework establishes that no additional work-authorisation delay applies.

### Language

Satisfied when the case meets the declared language-readiness criterion used by the frozen model version.

The current AUGUR B2 threshold is a modelling heuristic, not a legal requirement, so an approved calibration definition must state exactly how observed language readiness is evidenced.

### Skills

Satisfied when the case meets the essential-skill criterion used by the frozen CareerFit model version.

The current system uses declared ESCO essential-skill coverage. An approved observational definition must decide what evidence is sufficient for a retrospective case.

### Employment

Remote mode:

- satisfied when the existing portable-income arrangement remains viable for the target-country transition.

Local mode:

- satisfied when the person secures the local-employment condition defined by the frozen model.

An approved definition must specify whether this means offer accepted, contract signed, first working day, or another observable event.

### Financial

Satisfied when the household meets the financial-transition condition defined by the frozen model version.

The local-employment financial stage is currently incomplete, so this outcome cannot yet be frozen for local cases.

## 4. Why the viability outcome is not versioned yet

The dependency graph is clear, but several observed boundaries are not.

Unresolved items include:

- how language readiness is evidenced;
- how essential skill readiness is evidenced;
- which local-employment event counts as employment viability;
- the still-missing local financial-transition model;
- whether all conditions must be satisfied on the same date or whether the outcome date is the latest date on which each required condition first became satisfied without later regression.

Until these rules are resolved, `CALIBRATION_VIABILITY_OUTCOME_DEFINITION_VERSION` remains unset.

## 5. Calibration rule while definitions are draft

Development cases may still be collected for exploratory analysis.

They must not be described as holdout validation.

A development case should record as much provenance as possible about:

- the event treated as the start;
- the event treated as the observed outcome;
- any stage boundaries known with confidence.

Synthetic dates or reconstructed precision must not be added merely to make a case fit the schema.

## 6. Approval path

A future versioned definition should:

1. choose one start-event rule;
2. define observable evidence for every applicable dependency;
3. define the local-employment employment event;
4. define the financial-transition outcome;
5. define handling of already-in-progress stages;
6. define handling of regression after a stage first becomes ready;
7. receive immutable definition IDs;
8. update the calibration service constants;
9. be frozen before holdout collection begins.

Until then, the corresponding protocol blockers are intentionally unresolved.
