from __future__ import annotations

from app.models.profile import PersonalProfileResponse
from app.services.financial_fit import financial_fit
from app.services.legal_fit import legal_fit
from app.services.language_fit import language_fit
from app.services.career_fit import career_fit
from app.services.ttv_temporal import temporal_evidence_graph


STAGE_ORDER = [
    "legal_fit",
    "language_fit",
    "career_fit",
    "financial_fit",
]

# A duration model must be backed by validated temporal evidence before
# AUGUR can expose a time estimate. None means deliberately unavailable.
TEMPORAL_MODEL_VERSION = None


def ttv_status(
    profile: PersonalProfileResponse,
    target_country_iso3: str,
) -> dict:
    target = target_country_iso3.upper()
    legal = legal_fit(profile, target)
    financial = financial_fit(profile, target)
    language = language_fit(profile, target)
    career = career_fit(profile, target)

    temporal_evidence = temporal_evidence_graph(
        profile,
        target,
        legal,
        language,
        career,
        financial,
    )

    legal_ready = legal["status"] in {
        "domestic",
        "eu_free_movement_framework",
    }

    language_ready = bool(language["work_ready"])
    career_ready = bool(
        career["status"] == "evidence_available"
        and career.get("viability_evidence_ready")
    )

    if career["status"] != "evidence_available":
        career_reason = career["status"]
    elif not career.get("evidence_complete"):
        career_reason = "career_evidence_incomplete"
    elif not career.get("profile_skill_coverage_complete"):
        career_reason = "essential_skill_coverage_incomplete"
    elif not career.get("market_signal_supports_viability"):
        career_reason = "market_signal_not_supportive"
    else:
        career_reason = "ready"

    financial_ready = financial["status"] == "portable_income_comparable"

    stages = {
        "legal_fit": {
            "ready": legal_ready,
            "status": legal["status"],
            "evidence_state": "implemented",
            "reason": "ready" if legal_ready else legal["status"],
        },
        "language_fit": {
            "ready": language_ready,
            "status": language["status"],
            "evidence_state": "implemented",
            "reason": "ready" if language_ready else language["status"],
        },
        "career_fit": {
            "ready": career_ready,
            "status": (
                career["market_signal"]
                if career["status"] == "evidence_available"
                else career["status"]
            ),
            "evidence_state": (
                "implemented"
                if career.get("evidence_complete")
                else "partial"
            ),
            "reason": career_reason,
        },
        "financial_fit": {
            "ready": financial_ready,
            "status": financial["status"],
            "evidence_state": financial.get(
                "evidence_state",
                "implemented"
                if financial["status"] == "portable_income_comparable"
                else "partial",
            ),
            "reason": (
                "ready"
                if financial_ready
                else financial.get("reason") or financial["status"]
            ),
            "blockers": financial.get("blockers", []),
        },
    }

    blocked_by = [
        stage_id
        for stage_id in STAGE_ORDER
        if not stages[stage_id]["ready"]
    ]

    blocker_details = [
        {
            "stage_id": stage_id,
            "status": stages[stage_id]["status"],
            "evidence_state": stages[stage_id]["evidence_state"],
            "reason": stages[stage_id]["reason"],
            "blockers": stages[stage_id].get("blockers", []),
        }
        for stage_id in blocked_by
    ]

    evidence_complete = all(
        stages[stage_id]["evidence_state"] == "implemented"
        for stage_id in STAGE_ORDER
    )
    dependency_ready = not blocked_by and evidence_complete

    # Temporal evidence is deliberately separate from dependency readiness.
    # AUGUR does not yet have a validated duration model for language acquisition,
    # job search, legal processing or financial transition.
    temporal_evidence_state = (
        "implemented"
        if TEMPORAL_MODEL_VERSION is not None
        else "not_implemented"
    )
    ready_for_time_estimate = (
        dependency_ready
        and temporal_evidence_state == "implemented"
    )

    return {
        "target_country_iso3": target,
        "method": "ttv_dependency_graph_v1",
        "stage_order": STAGE_ORDER,
        "stages": stages,
        "blocked_by": blocked_by,
        "blocker_details": blocker_details,
        "dependency_ready": dependency_ready,
        "temporal_evidence_state": temporal_evidence_state,
        "temporal_model_version": TEMPORAL_MODEL_VERSION,
        "temporal_evidence_ready": temporal_evidence["calendar_ready"],
        "temporal_evidence": temporal_evidence,
        "candidate_time_range": temporal_evidence["candidate_range"],
        "estimate_status": (
            "available"
            if ready_for_time_estimate
            else "temporal_model_missing"
            if dependency_ready
            else "dependencies_blocked"
        ),
        "ready_for_time_estimate": ready_for_time_estimate,
        "time_estimate": None,
        "notes": [
            "TTV is a dependency graph, not a sum of arbitrary scores.",
            "Dependency readiness and temporal-estimation readiness are separate.",
            "No duration is produced until a validated temporal evidence model exists.",
            "A candidate temporal range may be exposed for validation without becoming an AUGUR estimate.",
            "CareerFit readiness requires complete declared essential-skill coverage and a supportive shortage signal.",
            "Local-employment FinancialFit remains partial when only structural gross earnings evidence is available.",
        ],
    }
