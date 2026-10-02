from __future__ import annotations

from app.models.profile import PersonalProfileResponse
from app.services.financial_fit import financial_fit
from app.services.legal_fit import legal_fit
from app.services.language_fit import language_fit
from app.services.career_fit import career_fit


STAGE_ORDER = [
    "legal_fit",
    "language_fit",
    "career_fit",
    "financial_fit",
]


def ttv_status(
    profile: PersonalProfileResponse,
    target_country_iso3: str,
) -> dict:
    target = target_country_iso3.upper()
    legal = legal_fit(profile, target)
    financial = financial_fit(profile, target)
    language = language_fit(profile, target)
    career = career_fit(profile, target)

    legal_ready = legal["status"] in {
        "domestic",
        "eu_free_movement_framework",
    }

    language_ready = bool(language["work_ready"])
    career_ready = bool(
        career.get("evidence_complete")
        and career["status"] == "evidence_available"
        and career["market_signal"] is not None
    )

    financial_ready = financial["status"] == "portable_income_comparable"

    stages = {
        "legal_fit": {
            "ready": legal_ready,
            "status": legal["status"],
            "evidence_state": "implemented",
        },
        "language_fit": {
            "ready": language_ready,
            "status": language["status"],
            "evidence_state": "implemented",
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
        },
        "financial_fit": {
            "ready": financial_ready,
            "status": financial["status"],
            "evidence_state": (
                "implemented"
                if financial["status"] in {
                    "portable_income_comparable",
                    "local_income_unknown",
                }
                else "partial"
            ),
        },
    }

    blocked_by = [
        stage_id
        for stage_id in STAGE_ORDER
        if not stages[stage_id]["ready"]
    ]

    evidence_complete = all(
        stages[stage_id]["evidence_state"] == "implemented"
        for stage_id in STAGE_ORDER
    )
    dependency_ready = not blocked_by and evidence_complete

    # Temporal evidence is deliberately separate from dependency readiness.
    # AUGUR does not yet have a validated duration model for language acquisition,
    # job search, legal processing or financial transition.
    temporal_evidence_state = "not_implemented"
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
        "dependency_ready": dependency_ready,
        "temporal_evidence_state": temporal_evidence_state,
        "ready_for_time_estimate": ready_for_time_estimate,
        "time_estimate": None,
        "notes": [
            "TTV is a dependency graph, not a sum of arbitrary scores.",
            "Dependency readiness and temporal-estimation readiness are separate.",
            "No duration is produced until a validated temporal evidence model exists.",
            "Local-employment FinancialFit remains partial when only structural gross earnings evidence is available.",
        ],
    }
