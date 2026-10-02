from __future__ import annotations

import json
from pathlib import Path

from app.models.profile import PersonalProfileResponse
from app.services.esco_match import match_profile_skills
from app.esco_store import search_occupations


EURES_EVIDENCE_PATH = (
    Path(__file__).resolve().parents[1]
    / "evidence"
    / "eures_lmi_2025.json"
)


def _load_eures_evidence() -> tuple[dict, dict]:
    payload = json.loads(EURES_EVIDENCE_PATH.read_text(encoding="utf-8"))
    countries = {
        country_iso3: {
            **config,
            "shortage_groups": set(config["shortage_groups"]),
            "surplus_groups": set(config["surplus_groups"]),
        }
        for country_iso3, config in payload["countries"].items()
    }
    metadata = {
        key: value
        for key, value in payload.items()
        if key != "countries"
    }
    return metadata, countries


EURES_EVIDENCE_METADATA, COUNTRY_EVIDENCE = _load_eures_evidence()
RULE_VERSION = EURES_EVIDENCE_METADATA["rule_version"]


ISCO_SUBMAJOR_TO_MARKET_GROUP = {
    "21": "science_engineering_professionals",
    "22": "health_professionals",
    "25": "ict_professionals",
    "26": "legal_social_cultural_professionals",
    "31": "science_engineering_associate_professionals",
    "33": "business_administration_associate_professionals",
    "35": "information_communications_technicians",
    "52": "sales_workers",
    "72": "metal_machinery_trades_workers",
    "81": "plant_machine_operators",
    "92": "agricultural_forestry_fishery_labourers",
}


ESCO_OCCUPATION_MATCH_THRESHOLD = 0.72


def resolve_esco_occupation(profession: str | None) -> dict:
    if not profession or not profession.strip():
        return {
            "status": "profession_missing",
            "selected": None,
            "candidates": [],
            "threshold": ESCO_OCCUPATION_MATCH_THRESHOLD,
        }

    candidates = search_occupations(profession, limit=5)
    selected = (
        candidates[0]
        if candidates and candidates[0]["match_score"] >= ESCO_OCCUPATION_MATCH_THRESHOLD
        else None
    )

    return {
        "status": "matched" if selected else "no_confident_match",
        "selected": selected,
        "candidates": candidates,
        "threshold": ESCO_OCCUPATION_MATCH_THRESHOLD,
    }

def classify_esco_market_group(
    occupation_match: dict,
) -> dict | None:
    selected = occupation_match.get("selected")
    if not selected:
        return None

    raw_isco = str(selected.get("isco_group") or selected.get("code") or "")
    digits = "".join(character for character in raw_isco if character.isdigit())
    if len(digits) < 2:
        return None

    submajor = digits[:2]
    group = ISCO_SUBMAJOR_TO_MARKET_GROUP.get(submajor)
    if group is None:
        return {
            "status": "isco_group_unmapped",
            "occupation_group": f"isco_{submajor}",
            "matched_terms": [],
            "mapping_method": "esco_isco_submajor",
            "isco_submajor": submajor,
        }

    return {
        "status": "mapped",
        "occupation_group": group,
        "matched_terms": [],
        "mapping_method": "esco_isco_submajor",
        "isco_submajor": submajor,
    }


OCCUPATION_RULES = [
    (
        "ict_professionals",
        [
            "software",
            "developer",
            "programmer",
            "systems analyst",
            "system analyst",
            "cybersecurity",
            "cyber security",
            "network engineer",
            "cloud engineer",
            "systems engineer",
            "system engineer",
            "it support",
            "support engineer",
            "system administrator",
            "systems administrator",
            "devops",
            "data engineer",
            "database administrator",
            "it engineer",
            "information technology",
            "ict",
        ],
    ),
    (
        "science_engineering_professionals",
        [
            "engineer",
            "engineering",
            "scientist",
            "architect",
        ],
    ),
    (
        "health_professionals",
        [
            "doctor",
            "physician",
            "nurse",
            "pharmacist",
            "dentist",
            "physiotherapist",
            "health professional",
        ],
    ),
    (
        "business_administration_associate_professionals",
        [
            "administrative",
            "administrator",
            "business support",
            "office manager",
            "bookkeeper",
        ],
    ),
    (
        "legal_social_cultural_professionals",
        [
            "lawyer",
            "solicitor",
            "legal",
            "social worker",
            "journalist",
            "translator",
        ],
    ),
    (
        "sales_workers",
        [
            "sales",
            "retail",
            "shop assistant",
            "cashier",
        ],
    ),
    (
        "metal_machinery_trades_workers",
        [
            "welder",
            "machinist",
            "mechanic",
            "metal worker",
            "toolmaker",
        ],
    ),
    (
        "plant_machine_operators",
        [
            "machine operator",
            "plant operator",
            "production operator",
        ],
    ),
    (
        "agricultural_forestry_fishery_labourers",
        [
            "farm worker",
            "agricultural worker",
            "forestry worker",
            "fishery worker",
        ],
    ),
]


def classify_occupation(profession: str | None) -> dict:
    if not profession or not profession.strip():
        return {
            "status": "profession_missing",
            "occupation_group": None,
            "matched_terms": [],
            "mapping_method": "keyword_fallback",
            "isco_submajor": None,
        }

    text = profession.strip().lower()
    matches = []

    for group, keywords in OCCUPATION_RULES:
        matched_terms = [
            keyword
            for keyword in keywords
            if keyword in text
        ]
        if matched_terms:
            matches.append(
                {
                    "occupation_group": group,
                    "matched_terms": matched_terms,
                }
            )

    if not matches:
        return {
            "status": "occupation_unmapped",
            "occupation_group": None,
            "matched_terms": [],
            "mapping_method": "keyword_fallback",
            "isco_submajor": None,
        }

    # Prefer the most specific match by longest matched keyword.
    matches.sort(
        key=lambda item: max(len(term) for term in item["matched_terms"]),
        reverse=True,
    )
    best = matches[0]

    return {
        "status": "mapped",
        "occupation_group": best["occupation_group"],
        "matched_terms": best["matched_terms"],
        "mapping_method": "keyword_fallback",
        "isco_submajor": None,
    }


def unit_group_market_signal(
    target_country_iso3: str,
    occupation_match: dict,
) -> dict | None:
    selected = occupation_match.get("selected")
    if not selected:
        return None

    raw_isco = str(selected.get("isco_group") or selected.get("code") or "")
    digits = "".join(character for character in raw_isco if character.isdigit())
    if len(digits) < 4:
        return None

    isco_unit = digits[:4]
    config = EURES_EVIDENCE_METADATA.get("unit_group_signals", {}).get(isco_unit)
    if config is None:
        return None

    target = target_country_iso3.upper()
    country_evidence = COUNTRY_EVIDENCE.get(target)
    eures_country_code = (
        country_evidence.get("eures_country_code")
        if country_evidence
        else None
    )
    if eures_country_code is None:
        return None

    if eures_country_code in config["shortage_countries"]:
        signal = "shortage"
    elif eures_country_code in config["surplus_countries"]:
        signal = "surplus"
    else:
        signal = "not_classified_as_shortage_or_surplus"

    return {
        "signal": signal,
        "isco_unit": isco_unit,
        "occupation_label": config["occupation_label"],
        "scope": "isco_unit_group",
    }


def career_fit(
    profile: PersonalProfileResponse,
    target_country_iso3: str,
) -> dict:
    target = target_country_iso3.upper()
    evidence = COUNTRY_EVIDENCE.get(target)
    occupation_match = resolve_esco_occupation(profile.profession)
    classification = (
        classify_esco_market_group(occupation_match)
        or classify_occupation(profile.profession)
    )
    esco_label = occupation_match["selected"]["preferred_label"] if occupation_match["selected"] else None

    if evidence is None:
        return {
            "target_country_iso3": target,
            "status": "country_evidence_missing",
            "occupation": classification,
            "market_signal": None,
            "rule_version": RULE_VERSION,
            "source": None,
            "occupation_match": occupation_match,
            "skill_match": {
                "status": "not_evaluated",
                "matched_skills": [],
                "missing_skills": [],
            },
            "evidence_complete": False,
            "profile_skill_coverage_complete": False,
            "market_signal_supports_viability": False,
            "viability_evidence_ready": False,
            "notes": [
                "No verified EURES country evidence is implemented for this target.",
                "No demand signal is inferred.",
            ],
        }

    group = classification["occupation_group"]

    if group is None:
        return {
            "target_country_iso3": target,
            "status": classification["status"],
            "occupation": classification,
            "market_signal": None,
            "rule_version": RULE_VERSION,
            "source": {
                "label": evidence["source_label"],
                "url": evidence["source_url"],
                "evidence_id": EURES_EVIDENCE_METADATA["evidence_id"],
                "report_year": EURES_EVIDENCE_METADATA["report_year"],
                "conditions_year": EURES_EVIDENCE_METADATA["conditions_year"],
                "report_url": EURES_EVIDENCE_METADATA["report_url"],
            },
            "occupation_match": occupation_match,
            "skill_match": {
                "status": "not_evaluated",
                "matched_skills": [],
                "missing_skills": [],
            },
            "evidence_complete": False,
            "profile_skill_coverage_complete": False,
            "market_signal_supports_viability": False,
            "viability_evidence_ready": False,
            "notes": [
                "CareerFit requires a mapped occupation group before EURES shortage/surplus evidence can be applied.",
                "No country-fit score is produced.",
            ],
        }

    unit_signal = unit_group_market_signal(target, occupation_match)

    if unit_signal is not None:
        market_signal = unit_signal["signal"]
        market_signal_scope = unit_signal["scope"]
        market_signal_isco = unit_signal["isco_unit"]
    elif group in evidence["shortage_groups"]:
        market_signal = "shortage"
        market_signal_scope = "broad_occupation_group"
        market_signal_isco = classification.get("isco_submajor")
    elif group in evidence["surplus_groups"]:
        market_signal = "surplus"
        market_signal_scope = "broad_occupation_group"
        market_signal_isco = classification.get("isco_submajor")
    else:
        market_signal = "not_classified_as_shortage_or_surplus"
        market_signal_scope = "broad_occupation_group"
        market_signal_isco = classification.get("isco_submajor")

    skill_match = (
        match_profile_skills(esco_label, profile.skills)
        if esco_label
        else {
            "status": "occupation_not_mapped_to_esco",
            "dataset_mode": None,
            "dataset_version": None,
            "occupation_label": None,
            "matched_skills": [],
            "missing_skills": [],
            "coverage": None,
            "evidence_complete": False,
        }
    )

    essential_total = skill_match.get("essential_skill_count") or 0
    essential_matched = skill_match.get("essential_skills_matched") or 0
    skill_coverage = skill_match.get("coverage")

    skill_evidence_complete = bool(
        skill_match.get("evidence_complete")
    )
    market_evidence_complete = unit_signal is not None

    profile_skill_coverage_complete = bool(
        skill_evidence_complete
        and essential_total > 0
        and essential_matched == essential_total
        and skill_coverage == 1.0
    )
    market_signal_supports_viability = bool(
        market_evidence_complete
        and market_signal == "shortage"
    )
    evidence_complete = bool(
        skill_evidence_complete
        and market_evidence_complete
    )
    viability_evidence_ready = bool(
        evidence_complete
        and profile_skill_coverage_complete
        and market_signal_supports_viability
    )

    return {
        "target_country_iso3": target,
        "status": "evidence_available",
        "occupation": classification,
        "market_signal": market_signal,
        "market_signal_scope": market_signal_scope,
        "market_signal_isco": market_signal_isco,
        "rule_version": RULE_VERSION,
        "source": {
            "label": evidence["source_label"],
            "url": evidence["source_url"],
            "evidence_id": EURES_EVIDENCE_METADATA["evidence_id"],
            "report_year": EURES_EVIDENCE_METADATA["report_year"],
            "conditions_year": EURES_EVIDENCE_METADATA["conditions_year"],
            "report_url": EURES_EVIDENCE_METADATA["report_url"],
        },
        "occupation_match": occupation_match,
        "skill_match": skill_match,
        "skill_evidence_complete": skill_evidence_complete,
        "market_evidence_complete": market_evidence_complete,
        "evidence_complete": evidence_complete,
        "profile_skill_coverage_complete": profile_skill_coverage_complete,
        "market_signal_supports_viability": market_signal_supports_viability,
        "viability_evidence_ready": viability_evidence_ready,
        "notes": [
            "EURES shortage/surplus groups are broad labour-market signals, not guarantees of job availability.",
            f"Country evidence uses versioned EURES labour-market information for {EURES_EVIDENCE_METADATA['conditions_year']} conditions, published in {EURES_EVIDENCE_METADATA['report_year']}.",
            "Salary, vacancy count, seniority, location and employer-specific skill requirements are not yet included.",
            "When ESCO resolves an occupation confidently, CareerFit uses verified EURES ISCO unit-group evidence first, then the ISCO sub-major group; keyword classification is only a fallback.",
            "Verified unit-group evidence takes precedence over broad occupational-group signals when both exist.",
            "Broad-group EURES evidence remains descriptive but does not count as complete CareerFit evidence for TTV.",
            "ISCO 25 ICT professionals and ISCO 35 information and communications technicians are kept distinct.",
            "Essential ESCO skills are treated as conservative profile-evidence requirements; missing declarations are not inferred as present.",
            "A shortage signal plus complete declared essential-skill coverage is an evidence gate, not a guarantee of employment.",
            "No country ranking or composite score is produced.",
        ],
    }
