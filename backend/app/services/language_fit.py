from __future__ import annotations

from app.catalog import country_config
from app.models.profile import PersonalProfileResponse
from app.esco_store import esco_status, occupation_language_skill_rows
from app.services.career_fit import resolve_esco_occupation


CEFR_ORDER = {
    "A1": 1,
    "A2": 2,
    "B1": 3,
    "B2": 4,
    "C1": 5,
    "C2": 6,
}

WORK_READY_THRESHOLD = "B2"


def occupation_language_evidence(
    profile: PersonalProfileResponse,
) -> dict:
    if not profile.profession or not profile.profession.strip():
        return {
            "status": "profession_missing",
            "occupation_match": None,
            "occupation_label": None,
            "dataset_mode": None,
            "dataset_version": None,
            "skills": [],
            "essential_skill_count": 0,
            "optional_skill_count": 0,
            "evidence_complete": False,
        }

    occupation_match = resolve_esco_occupation(profile.profession)
    selected = occupation_match.get("selected")

    if not selected:
        return {
            "status": "no_confident_occupation_match",
            "occupation_match": occupation_match,
            "occupation_label": None,
            "dataset_mode": None,
            "dataset_version": None,
            "skills": [],
            "essential_skill_count": 0,
            "optional_skill_count": 0,
            "evidence_complete": False,
        }

    status = esco_status()
    rows = occupation_language_skill_rows(selected["preferred_label"])
    skills = [
        {
            "skill_uri": row["skill_uri"],
            "skill_label": row["skill_label"],
            "relation_type": row["relation_type"],
        }
        for row in rows
    ]

    essential_count = sum(
        1
        for item in skills
        if item["relation_type"] == "essential"
    )
    optional_count = sum(
        1
        for item in skills
        if item["relation_type"] != "essential"
    )

    if status["mode"] != "full":
        evidence_status = "partial_dataset"
        evidence_complete = False
    elif skills:
        evidence_status = "occupation_language_evidence_available"
        evidence_complete = True
    else:
        evidence_status = "no_occupation_language_evidence_listed"
        evidence_complete = True

    return {
        "status": evidence_status,
        "occupation_match": occupation_match,
        "occupation_label": selected["preferred_label"],
        "dataset_mode": status["mode"],
        "dataset_version": status["version"],
        "skills": skills,
        "essential_skill_count": essential_count,
        "optional_skill_count": optional_count,
        "evidence_complete": evidence_complete,
    }


def language_fit(
    profile: PersonalProfileResponse,
    target_country_iso3: str,
) -> dict:
    target = target_country_iso3.upper()
    country = country_config(target)
    target_languages = country.get("labour_market_languages", [])
    occupation_evidence = occupation_language_evidence(profile)

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
        "method": "labour_market_language_heuristic_v2",
        "occupation_language_evidence": occupation_evidence,
        "notes": [
            "B2 is an AUGUR modelling heuristic for general professional work-readiness, not a legal requirement.",
            "ESCO language-skill relationships are occupation evidence and do not encode a CEFR requirement.",
            "ESCO evidence does not override the declared-language heuristic.",
            "Occupation-specific language evidence from live job postings is not implemented yet.",
            "No country-fit score is produced.",
        ],
    }
