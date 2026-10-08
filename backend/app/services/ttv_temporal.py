from __future__ import annotations

import math

from app.db.analytics import latest_labour_job_transition
from app.models.profile import PersonalProfileResponse
from app.services.ttv_calibration import calibration_status


TEMPORAL_EVIDENCE_ENGINE_VERSION = "ttv-temporal-evidence-v1"

TTV_ESTIMATION_SCOPE_V1 = {
    "scope_id": "ttv-estimation-scope-v1",
    "employment_mode": "preserved_remote_income_only",
    "essential_skill_gap": "none_allowed",
    "legal_scope": "domestic_or_eu_free_movement_currently_supported",
    "language_scope": "declared_cefr_with_explicit_weekly_study_intensity_when_below_b2",
    "reason": (
        "AUGUR v1 candidate timing is intentionally bounded to cases where "
        "essential skills are already covered and portable remote income is preserved."
    ),
}

TEMPORAL_MODEL_VALIDATION_GATES = {
    "legal_domestic_eu_timing": {
        "state": "supported",
        "reason": "domestic_and_eu_work_right_timing_is_explicit",
    },
    "language_guided_hours": {
        "state": "supported",
        "reason": "published_cefr_guided_learning_hour_ranges",
    },
    "language_calendar_intensity": {
        "state": "supported",
        "reason": "calendar_conversion_requires_explicit_user_hours_per_week",
    },
    "skill_gap_duration": {
        "state": "scope_bounded",
        "reason": "v1_estimation_scope_requires_declared_essential_skill_coverage_complete",
    },
    "remote_income_transition": {
        "state": "supported",
        "reason": "preserved_remote_income_requires_no_job_search_transition",
    },
    "local_employment_transition": {
        "state": "scope_bounded",
        "reason": "v1_estimation_scope_excludes_local_employment_search_duration",
    },
    "local_financial_transition": {
        "state": "scope_bounded",
        "reason": "v1_estimation_scope_requires_preserved_portable_income",
    },
    "composition_dependency_graph": {
        "state": "supported",
        "reason": "v1_scope_has_parallel_preparation_with_zero_employment_and_financial_transition_stages",
    },
    "external_calibration": {
        "state": "missing",
        "reason": "candidate_ranges_not_calibrated_against_observed_relocation_outcomes",
    },
}

# Cambridge English guided-learning-hour guidance, cumulative from beginner.
# These are planning ranges, not guarantees of calendar time.
CEFR_CUMULATIVE_GUIDED_HOURS = {
    "A1": (90, 100),
    "A2": (180, 200),
    "B1": (350, 400),
    "B2": (500, 600),
    "C1": (700, 800),
    "C2": (1000, 1200),
}

LANGUAGE_TARGET_LEVEL = "B2"
LANGUAGE_SOURCE = {
    "label": "Cambridge English — Guided learning hours",
    "url": "https://support.cambridgeenglish.org/hc/en-gb/articles/202838506-Guided-learning-hours",
    "retrieved_basis": "published guidance",
}


def temporal_model_validation_status() -> dict:
    gates = {
        gate_id: dict(config)
        for gate_id, config in TEMPORAL_MODEL_VALIDATION_GATES.items()
    }

    calibration = calibration_status()
    if calibration.get("externally_calibrated"):
        gates["external_calibration"] = {
            "state": "supported",
            "reason": (
                "sealed_holdout_passed_predeclared_criteria_and_"
                "representativeness_review"
            ),
            "protocol_version": calibration.get("protocol_version"),
            "holdout_sha256": (
                calibration.get("holdout_seal") or {}
            ).get("holdout_sha256"),
        }
    else:
        gates["external_calibration"] = {
            "state": "missing",
            "reason": "external_calibration_requirements_not_complete",
            "blockers": (
                calibration.get("activation_readiness") or {}
            ).get("blockers", []),
        }
    accepted_states = {"supported", "scope_bounded"}
    blockers = [
        gate_id
        for gate_id, config in gates.items()
        if config["state"] not in accepted_states
    ]
    experimental = [
        gate_id
        for gate_id, config in gates.items()
        if config["state"] == "experimental"
    ]
    missing = [
        gate_id
        for gate_id, config in gates.items()
        if config["state"] == "missing"
    ]
    scope_bounded = [
        gate_id
        for gate_id, config in gates.items()
        if config["state"] == "scope_bounded"
    ]

    return {
        "engine_version": TEMPORAL_EVIDENCE_ENGINE_VERSION,
        "ready_for_versioning": len(blockers) == 0,
        "gates": gates,
        "blockers": blockers,
        "experimental": experimental,
        "missing": missing,
        "scope_bounded": scope_bounded,
        "model_scope": TTV_ESTIMATION_SCOPE_V1,
        "calibration": {
            "protocol_version": calibration.get("protocol_version"),
            "externally_calibrated": calibration.get("externally_calibrated", False),
            "holdout_seal": calibration.get("holdout_seal"),
            "holdout_review": calibration.get("holdout_review"),
            "holdout_acceptance": calibration.get("holdout_acceptance"),
            "activation_readiness": calibration.get("activation_readiness"),
        },
        "notes": [
            "Supported means the evidence path is implemented with an explicit basis; it does not imply external calibration.",
            "Scope-bounded means AUGUR deliberately excludes cases that would require an unvalidated duration assumption instead of inventing one.",
            "Experimental gates must be validated or replaced before a published TTV model can be versioned.",
            "Missing gates have no accepted duration model yet.",
        ],
    }


def ttv_estimation_scope_status(
    profile: PersonalProfileResponse,
    career: dict,
    financial: dict,
) -> dict:
    blockers = []

    if not career.get("viability_evidence_ready"):
        blockers.append("essential_skill_or_market_viability_not_ready")

    if not profile.remote_work:
        blockers.append("local_employment_mode_outside_v1_scope")

    if financial.get("status") != "portable_income_comparable":
        blockers.append("portable_income_not_verified")

    return {
        "scope_id": TTV_ESTIMATION_SCOPE_V1["scope_id"],
        "in_scope": not blockers,
        "blockers": blockers,
        "definition": TTV_ESTIMATION_SCOPE_V1,
    }


def _zero_stage(reason: str, source: dict | None = None) -> dict:
    return {
        "status": "available",
        "weeks_min": 0,
        "weeks_max": 0,
        "reason": reason,
        "source": source,
    }


def _unavailable_stage(reason: str, source: dict | None = None) -> dict:
    return {
        "status": "unavailable",
        "weeks_min": None,
        "weeks_max": None,
        "reason": reason,
        "source": source,
    }


def legal_temporal_evidence(legal: dict) -> dict:
    status = legal.get("status")

    if status == "domestic":
        return _zero_stage("domestic_no_cross_border_delay")

    if status == "eu_free_movement_framework":
        return _zero_stage(
            "eu_work_right_does_not_wait_for_residence_registration",
            {
                "label": "Your Europe — Working abroad / residence rights",
                "url": "https://europa.eu/youreurope/citizens/work/work-abroad/index_en.htm",
            },
        )

    return _unavailable_stage("legal_timing_not_verified_for_profile")


def _declared_target_cefr(language: dict) -> str | None:
    matches = language.get("matches") or []
    levels = [
        item.get("declared_cefr")
        for item in matches
        if item.get("declared_cefr")
    ]
    if not levels:
        return None

    order = list(CEFR_CUMULATIVE_GUIDED_HOURS)
    ranked = [
        level.upper()
        for level in levels
        if level.upper() in CEFR_CUMULATIVE_GUIDED_HOURS
    ]
    if not ranked:
        return None

    return max(ranked, key=order.index)


def language_temporal_evidence(
    profile: PersonalProfileResponse,
    language: dict,
) -> dict:
    if language.get("work_ready"):
        return _zero_stage(
            "target_language_already_meets_augur_work_ready_heuristic",
            LANGUAGE_SOURCE,
        )

    current_level = _declared_target_cefr(language)
    if current_level is None:
        return {
            **_unavailable_stage(
                "target_language_cefr_required_for_temporal_estimate",
                LANGUAGE_SOURCE,
            ),
            "current_cefr": None,
            "target_cefr": LANGUAGE_TARGET_LEVEL,
            "guided_hours_min": None,
            "guided_hours_max": None,
            "weekly_study_hours": None,
        }

    target_min, target_max = CEFR_CUMULATIVE_GUIDED_HOURS[LANGUAGE_TARGET_LEVEL]
    current_min, current_max = CEFR_CUMULATIVE_GUIDED_HOURS[current_level]

    guided_min = max(0, target_min - current_max)
    guided_max = max(0, target_max - current_min)

    raw_weekly = profile.preferences.get("language_study_hours_per_week")
    weekly_hours = (
        float(raw_weekly)
        if isinstance(raw_weekly, (int, float))
        and not isinstance(raw_weekly, bool)
        and 0 < float(raw_weekly) <= 80
        else None
    )

    result = {
        "current_cefr": current_level,
        "target_cefr": LANGUAGE_TARGET_LEVEL,
        "guided_hours_min": guided_min,
        "guided_hours_max": guided_max,
        "weekly_study_hours": weekly_hours,
        "source": LANGUAGE_SOURCE,
    }

    if weekly_hours is None:
        return {
            **result,
            "status": "guided_hours_available_calendar_missing",
            "weeks_min": None,
            "weeks_max": None,
            "reason": "language_study_hours_per_week_missing",
        }

    return {
        **result,
        "status": "available",
        "weeks_min": math.ceil(guided_min / weekly_hours),
        "weeks_max": math.ceil(guided_max / weekly_hours),
        "reason": "cambridge_guided_hours_with_user_study_intensity",
    }


def skills_temporal_evidence(career: dict) -> dict:
    if career.get("viability_evidence_ready"):
        return _zero_stage("declared_essential_skill_coverage_complete")

    if career.get("evidence_complete"):
        return _unavailable_stage(
            "essential_skill_gap_training_duration_not_modelled"
        )

    return _unavailable_stage("career_skill_evidence_incomplete")


def financial_temporal_evidence(financial: dict) -> dict:
    if financial.get("status") == "portable_income_comparable":
        return _zero_stage("portable_income_financial_evidence_ready")

    return _unavailable_stage(
        "financial_transition_duration_not_modelled_for_current_status"
    )


def _quarters_to_cumulative_probability(
    quarterly_probability: float,
    target_probability: float,
) -> int | None:
    if not (0 < quarterly_probability <= 1):
        return None
    if not (0 < target_probability < 1):
        return None
    if quarterly_probability == 1:
        return 1

    return math.ceil(
        math.log(1 - target_probability)
        / math.log(1 - quarterly_probability)
    )


def _preferred_job_transition_age_group(age: int | None) -> str | None:
    if age is None:
        return "Y15-74"
    if 15 <= age <= 24:
        return "Y15-24"
    if 25 <= age <= 54:
        return "Y25-54"
    if 55 <= age <= 74:
        return "Y55-74"
    return None


def employment_temporal_evidence(
    profile: PersonalProfileResponse,
    target_country_iso3: str,
    financial: dict,
    career: dict,
) -> dict:
    if (
        profile.remote_work
        and financial.get("status") == "portable_income_comparable"
    ):
        return _zero_stage("existing_remote_income_preserved")

    if not career.get("viability_evidence_ready"):
        return _unavailable_stage(
            "career_viability_required_before_job_search_baseline"
        )

    preferred_age_group = _preferred_job_transition_age_group(
        profile.age
    )
    if preferred_age_group is None:
        return {
            **_unavailable_stage(
                "profile_age_outside_eurostat_transition_population"
            ),
            "profile_age": profile.age,
            "requested_age_group": None,
        }

    row = latest_labour_job_transition(
        target_country_iso3,
        age_group=preferred_age_group,
    )
    age_specific = row is not None and preferred_age_group != "Y15-74"

    if row is None and preferred_age_group != "Y15-74":
        row = latest_labour_job_transition(
            target_country_iso3,
            age_group="Y15-74",
        )
        age_specific = False

    if row is None:
        return {
            **_unavailable_stage(
                "eurostat_job_transition_baseline_missing"
            ),
            "profile_age": profile.age,
            "requested_age_group": preferred_age_group,
        }

    quarterly_probability = float(row["probability_pct"]) / 100.0
    median_quarters = _quarters_to_cumulative_probability(
        quarterly_probability,
        0.50,
    )
    upper_quarters = _quarters_to_cumulative_probability(
        quarterly_probability,
        0.80,
    )

    if median_quarters is None or upper_quarters is None:
        return _unavailable_stage(
            "invalid_job_transition_probability"
        )

    return {
        "status": "available",
        "weeks_min": median_quarters * 13,
        "weeks_max": upper_quarters * 13,
        "reason": "eurostat_experimental_job_transition_baseline",
        "source": {
            "label": "Eurostat — unemployment to employment transition probability",
            "dataset_id": row["dataset_id"],
            "source_id": row["source_id"],
            "period": row["period"],
            "age_group": row["age_group"],
            "duration_group": row["duration_group"],
        },
        "profile_age": profile.age,
        "requested_age_group": preferred_age_group,
        "age_specific_baseline": age_specific,
        "quarterly_transition_probability_pct": row["probability_pct"],
        "range_definition": {
            "lower_cumulative_probability": 0.50,
            "upper_cumulative_probability": 0.80,
            "constant_quarterly_hazard_assumption": True,
        },
        "limitations": [
            "Experimental country-level transition probability.",
            "Age-specific evidence is used when the matching Eurostat age class exists; otherwise AUGUR falls back to ages 15–74.",
            "Not occupation-specific and not an individual job-offer forecast.",
            "Quarter-to-quarter probability is treated as constant only for AUGUR range modelling.",
        ],
    }


def compose_temporal_stages(stages: dict[str, dict]) -> dict | None:
    if not all(
        stage["status"] == "available"
        for stage in stages.values()
    ):
        return None

    preparation_ids = ["legal", "language", "skills"]
    preparation_min = max(
        int(stages[stage_id]["weeks_min"])
        for stage_id in preparation_ids
    )
    preparation_max = max(
        int(stages[stage_id]["weeks_max"])
        for stage_id in preparation_ids
    )

    employment_min = int(stages["employment"]["weeks_min"])
    employment_max = int(stages["employment"]["weeks_max"])
    financial_min = int(stages["financial"]["weeks_min"])
    financial_max = int(stages["financial"]["weeks_max"])

    return {
        "weeks_min": preparation_min + employment_min + financial_min,
        "weeks_max": preparation_max + employment_max + financial_max,
        "composition": "critical_path_v1",
        "stage_groups": {
            "preparation_parallel": preparation_ids,
            "employment_after_preparation": ["employment"],
            "financial_after_employment": ["financial"],
        },
    }


def temporal_evidence_graph(
    profile: PersonalProfileResponse,
    target_country_iso3: str,
    legal: dict,
    language: dict,
    career: dict,
    financial: dict,
) -> dict:
    scope = ttv_estimation_scope_status(
        profile,
        career,
        financial,
    )

    stages = {
        "legal": legal_temporal_evidence(legal),
        "language": language_temporal_evidence(profile, language),
        "skills": skills_temporal_evidence(career),
        "financial": financial_temporal_evidence(financial),
        "employment": employment_temporal_evidence(
            profile,
            target_country_iso3,
            financial,
            career,
        ),
    }

    calendar_ready = all(
        stage["status"] == "available"
        for stage in stages.values()
    )

    unavailable = [
        stage_id
        for stage_id, stage in stages.items()
        if stage["status"] != "available"
    ]

    candidate_range = (
        compose_temporal_stages(stages)
        if calendar_ready
        else None
    )

    return {
        "engine_version": TEMPORAL_EVIDENCE_ENGINE_VERSION,
        "estimation_scope": scope,
        "calendar_ready": calendar_ready and scope["in_scope"],
        "stages": stages,
        "unavailable_stages": unavailable,
        "candidate_range": candidate_range if scope["in_scope"] else None,
        "notes": [
            "Legal, language and skills preparation may progress in parallel; employment follows preparation and financial transition follows employment in the candidate critical path.",
            "Guided language hours are planning guidance and may vary by learner.",
            "This evidence engine does not activate AUGUR TTV until the temporal model is explicitly versioned.",
            "Candidate timing is withheld outside the explicit v1 estimation scope instead of assigning unvalidated skill-gap or local-financial durations.",
        ],
    }
