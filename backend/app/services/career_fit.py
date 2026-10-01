from __future__ import annotations

from app.models.profile import PersonalProfileResponse


RULE_VERSION = "EURES_LMI_2024_AS_PUBLISHED_2025"

COUNTRY_EVIDENCE = {
    "ESP": {
        "source_url": "https://eures.europa.eu/living-and-working/labour-market-information/labour-market-information-spain_en",
        "source_label": "EURES Labour Market Information: Spain",
        "shortage_groups": {
            "health_professionals",
            "plant_machine_operators",
            "agricultural_forestry_fishery_labourers",
        },
        "surplus_groups": {
            "science_engineering_professionals",
            "business_administration_associate_professionals",
            "science_engineering_associate_professionals",
        },
    },
    "PRT": {
        "source_url": "https://eures.europa.eu/living-and-working/labour-market-information/labour-market-information-portugal_en",
        "source_label": "EURES Labour Market Information: Portugal",
        "shortage_groups": {
            "health_professionals",
            "metal_machinery_trades_workers",
            "ict_professionals",
        },
        "surplus_groups": {
            "business_administration_associate_professionals",
            "legal_social_cultural_professionals",
            "sales_workers",
        },
    },
    "IRL": {
        "source_url": "https://eures.europa.eu/living-and-working/labour-market-information/labour-market-information-ireland_en",
        "source_label": "EURES Labour Market Information: Ireland",
        "shortage_groups": {
            "science_engineering_professionals",
            "ict_professionals",
            "health_professionals",
        },
        "surplus_groups": set(),
    },
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
    }


def career_fit(
    profile: PersonalProfileResponse,
    target_country_iso3: str,
) -> dict:
    target = target_country_iso3.upper()
    evidence = COUNTRY_EVIDENCE.get(target)
    classification = classify_occupation(profile.profession)

    if evidence is None:
        return {
            "target_country_iso3": target,
            "status": "country_evidence_missing",
            "occupation": classification,
            "market_signal": None,
            "rule_version": RULE_VERSION,
            "source": None,
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
            },
            "notes": [
                "CareerFit requires a mapped occupation group before EURES shortage/surplus evidence can be applied.",
                "No country-fit score is produced.",
            ],
        }

    if group in evidence["shortage_groups"]:
        market_signal = "shortage"
    elif group in evidence["surplus_groups"]:
        market_signal = "surplus"
    else:
        market_signal = "not_classified_as_shortage_or_surplus"

    return {
        "target_country_iso3": target,
        "status": "evidence_available",
        "occupation": classification,
        "market_signal": market_signal,
        "rule_version": RULE_VERSION,
        "source": {
            "label": evidence["source_label"],
            "url": evidence["source_url"],
        },
        "notes": [
            "EURES shortage/surplus groups are broad labour-market signals, not guarantees of job availability.",
            "Country evidence is based on the latest implemented EURES labour-market information for 2024 conditions.",
            "Salary, vacancy count, seniority, location and employer-specific skill requirements are not yet included.",
            "No country ranking or composite score is produced.",
        ],
    }
