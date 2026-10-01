from __future__ import annotations

from app.models.profile import PersonalProfileResponse
from app.services.financial_fit import financial_fit
from app.services.legal_fit import legal_fit
from app.services.language_fit import language_fit


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

    legal_ready = legal["status"] in {
        "domestic",
        "eu_free_movement_framework",
    }

    language_ready = bool(language["work_ready"])
    career_ready = bool(profile.profession and profile.skills)

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
                "profile_inputs_present"
                if career_ready
                else "profile_inputs_missing"
            ),
            "evidence_state": "country_evidence_pending",
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
            "LanguageFit uses a country-language CEFR heuristic; CareerFit country evidence is still pending.",
        ],
    }
