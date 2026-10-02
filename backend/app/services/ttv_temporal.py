from __future__ import annotations

import math

from app.db.analytics import latest_labour_job_transition
from app.models.profile import PersonalProfileResponse


TEMPORAL_EVIDENCE_ENGINE_VERSION = "ttv-temporal-evidence-v1"

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
        "state": "missing",
        "reason": "training_duration_for_missing_essential_skills_not_modelled",
    },
    "remote_income_transition": {
        "state": "supported",
        "reason": "preserved_remote_income_requires_no_job_search_transition",
    },
    "local_employment_transition": {
        "state": "experimental",
        "reason": "country_level_transition_probability_not_occupation_specific",
    },
    "local_financial_transition": {
        "state": "missing",
        "reason": "occupation_specific_net_income_household_budget_and_transition_costs_incomplete",
    },
    "composition_parallel_max": {
        "state": "experimental",
        "reason": "parallel_stage_composition_not_externally_calibrated",
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
    blockers = [
        gate_id
        for gate_id, config in gates.items()
        if config["state"] != "supported"
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

    return {
        "engine_version": TEMPORAL_EVIDENCE_ENGINE_VERSION,
        "ready_for_versioning": len(blockers) == 0,
        "gates": gates,
        "blockers": blockers,
        "experimental": experimental,
        "missing": missing,
        "notes": [
            "Supported means the evidence path is implemented with an explicit basis; it does not imply external calibration.",
            "Experimental gates must be validated or replaced before a published TTV model can be versioned.",
            "Missing gates have no accepted duration model yet.",
        ],
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

    row = latest_labour_job_transition(target_country_iso3)
    if row is None:
        return _unavailable_stage(
            "eurostat_job_transition_baseline_missing"
        )

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
        "quarterly_transition_probability_pct": row["probability_pct"],
        "range_definition": {
            "lower_cumulative_probability": 0.50,
            "upper_cumulative_probability": 0.80,
            "constant_quarterly_hazard_assumption": True,
        },
        "limitations": [
            "Experimental country-level transition probability.",
            "Not occupation-specific and not an individual job-offer forecast.",
            "Quarter-to-quarter probability is treated as constant only for AUGUR range modelling.",
        ],
    }


def temporal_evidence_graph(
    profile: PersonalProfileResponse,
    target_country_iso3: str,
    legal: dict,
    language: dict,
    career: dict,
    financial: dict,
) -> dict:
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

    candidate_range = None
    if calendar_ready:
        candidate_range = {
            "weeks_min": max(
                int(stage["weeks_min"])
                for stage in stages.values()
            ),
            "weeks_max": max(
                int(stage["weeks_max"])
                for stage in stages.values()
            ),
            "composition": "parallel_max",
        }

    return {
        "engine_version": TEMPORAL_EVIDENCE_ENGINE_VERSION,
        "calendar_ready": calendar_ready,
        "stages": stages,
        "unavailable_stages": unavailable,
        "candidate_range": candidate_range,
        "notes": [
            "Stage durations are composed in parallel using the maximum duration, not summed.",
            "Guided language hours are planning guidance and may vary by learner.",
            "This evidence engine does not activate AUGUR TTV until the temporal model is explicitly versioned.",
        ],
    }
