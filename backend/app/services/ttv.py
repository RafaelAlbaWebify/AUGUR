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
    career_ready = (
        career["status"] == "evidence_available"
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
                if career["status"] == "evidence_available"
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

    return {
        "target_country_iso3": target,
        "method": "ttv_dependency_graph_v1",
        "stage_order": STAGE_ORDER,
        "stages": stages,
        "blocked_by": blocked_by,
        "ready_for_time_estimate": not blocked_by and evidence_complete,
        "time_estimate": None,
        "notes": [
            "TTV is a dependency graph, not a sum of arbitrary scores.",
            "No time estimate is produced until all required country evidence layers are implemented.",
            "LanguageFit uses a country-language CEFR heuristic; CareerFit uses implemented EURES shortage/surplus evidence.",
        ],
    }
