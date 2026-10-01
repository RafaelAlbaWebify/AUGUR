from __future__ import annotations

from app.catalog import country_config
from app.models.profile import PersonalProfileResponse


CEFR_ORDER = {
    "A1": 1,
    "A2": 2,
    "B1": 3,
    "B2": 4,
    "C1": 5,
    "C2": 6,
}

WORK_READY_THRESHOLD = "B2"


def language_fit(
    profile: PersonalProfileResponse,
    target_country_iso3: str,
) -> dict:
    target = target_country_iso3.upper()
    country = country_config(target)
    target_languages = country.get("labour_market_languages", [])

    declared = {
        item.language.strip().lower(): (
            item.cefr.upper()
            if item.cefr
            else None
        )
        for item in profile.languages
        if item.language.strip()
    }

    matches = []

    for language in target_languages:
        cefr = declared.get(language.lower())
        level = CEFR_ORDER.get(cefr or "")
        threshold = CEFR_ORDER[WORK_READY_THRESHOLD]

        matches.append(
            {
                "language": language,
                "declared_cefr": cefr,
                "meets_work_ready_heuristic": (
                    level is not None and level >= threshold
                ),
            }
        )

    work_ready = any(
        item["meets_work_ready_heuristic"]
        for item in matches
    )

    language_present_without_level = any(
        item["declared_cefr"] is None
        and item["language"].lower() in declared
        for item in matches
    )

    if work_ready:
        status = "work_ready_heuristic"
    elif language_present_without_level:
        status = "cefr_missing"
    elif any(item["declared_cefr"] for item in matches):
        status = "language_gap"
    else:
        status = "target_language_missing"

    return {
        "target_country_iso3": target,
        "status": status,
        "target_languages": target_languages,
        "matches": matches,
        "work_ready_threshold": WORK_READY_THRESHOLD,
        "work_ready": work_ready,
        "method": "labour_market_language_heuristic_v1",
        "notes": [
            "B2 is an AUGUR modelling heuristic for general professional work-readiness, not a legal requirement.",
            "Occupation-specific language evidence from job postings is not implemented yet.",
            "No country-fit score is produced.",
        ],
    }
