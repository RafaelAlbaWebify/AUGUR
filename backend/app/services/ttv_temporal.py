from __future__ import annotations

import math

from app.models.profile import PersonalProfileResponse


TEMPORAL_EVIDENCE_ENGINE_VERSION = "ttv-temporal-evidence-v1"

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


def employment_temporal_evidence(
    profile: PersonalProfileResponse,
    financial: dict,
) -> dict:
    if (
        profile.remote_work
        and financial.get("status") == "portable_income_comparable"
    ):
        return _zero_stage("existing_remote_income_preserved")

    return _unavailable_stage(
        "local_job_search_temporal_baseline_not_yet_integrated"
    )


def temporal_evidence_graph(
    profile: PersonalProfileResponse,
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
        "employment": employment_temporal_evidence(profile, financial),
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
