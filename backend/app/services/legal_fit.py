from __future__ import annotations

from app.catalog import EU_MEMBER_ISO3
from app.models.profile import PersonalProfileResponse
from app.services.country import country_metadata


RULE_VERSION = "2026-10-01"

SOURCES = [
    {
        "title": "Your Europe — residence rights when living abroad in the EU",
        "url": "https://europa.eu/youreurope/citizens/residence/residence-rights/index_en.htm",
    },
    {
        "title": "European Commission — free movement of EU nationals",
        "url": "https://employment-social-affairs.ec.europa.eu/policies-and-activities/moving-working-europe/working-another-eu-country/free-movement-eu-nationals_en",
    },
]


def legal_fit(
    profile: PersonalProfileResponse,
    target_country_iso3: str,
) -> dict:
    target = target_country_iso3.upper()
    country = country_metadata(target)

    if not profile.current_country:
        return {
            "target_country_iso3": target,
            "status": "insufficient_profile",
            "framework": None,
            "work_permit_required": None,
            "short_stay": None,
            "long_stay": None,
            "rule_version": RULE_VERSION,
            "sources": SOURCES,
            "notes": [
                "Current country is required to distinguish domestic from cross-border rules.",
                "No visa or residence eligibility is inferred.",
            ],
        }

    origin = profile.current_country.upper()

    if origin == target:
        return {
            "target_country_iso3": target,
            "status": "domestic",
            "framework": "domestic_rules",
            "work_permit_required": None,
            "short_stay": None,
            "long_stay": None,
            "rule_version": RULE_VERSION,
            "sources": [],
            "notes": [
                "Domestic status detected; cross-border free-movement logic is not applied.",
            ],
        }

    citizenships = {value.upper() for value in profile.citizenships}
    eu_citizenship = sorted(citizenships & EU_MEMBER_ISO3)

    if country.get("eu_member") and eu_citizenship:
        return {
            "target_country_iso3": target,
            "status": "eu_free_movement_framework",
            "framework": "EU_free_movement",
            "basis_citizenships": eu_citizenship,
            "work_permit_required": False,
            "short_stay": {
                "up_to_months": 3,
                "residence_registration_generally_required": False,
                "presence_reporting_may_apply": True,
            },
            "long_stay": {
                "registration_may_be_required": True,
                "conditions_depend_on_status": True,
                "statuses": [
                    "worker",
                    "self_employed",
                    "jobseeker",
                    "student",
                    "economically_inactive",
                ],
            },
            "rule_version": RULE_VERSION,
            "sources": SOURCES,
            "notes": [
                "EU free movement is a legal framework, not an automatic confirmation that every long-stay condition is met.",
                "Country-specific registration formalities still apply.",
                "Professional qualification recognition may be required for regulated occupations.",
            ],
        }

    return {
        "target_country_iso3": target,
        "status": "country_specific_rules_required",
        "framework": None,
        "work_permit_required": None,
        "short_stay": None,
        "long_stay": None,
        "rule_version": RULE_VERSION,
        "sources": SOURCES,
        "notes": [
            "AUGUR does not yet have a verified country-specific immigration rule for this citizenship/target combination.",
            "No visa or residence eligibility is inferred.",
        ],
    }
