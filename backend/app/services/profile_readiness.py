from __future__ import annotations

from app.models.profile import PersonalProfileResponse


REQUIREMENTS = {
    "legal_fit": {
        "label": "LegalFit",
        "fields": ["current_country", "citizenships"],
    },
    "career_fit": {
        "label": "CareerFit",
        "fields": ["profession", "skills"],
    },
    "language_fit": {
        "label": "LanguageFit",
        "fields": ["languages"],
    },
    "financial_fit": {
        "label": "FinancialFit",
        "fields": [
            "current_country",
            "monthly_net_income",
        ],
    },
}


def _has_value(profile: PersonalProfileResponse, field: str) -> bool:
    value = getattr(profile, field)

    if value is None:
        return False

    if isinstance(value, (list, dict, str)):
        return len(value) > 0

    return True


def profile_readiness(profile: PersonalProfileResponse) -> dict:
    modules = {}

    for module_id, config in REQUIREMENTS.items():
        missing = [
            field
            for field in config["fields"]
            if not _has_value(profile, field)
        ]
        completed = len(config["fields"]) - len(missing)

        modules[module_id] = {
            "label": config["label"],
            "ready": len(missing) == 0,
            "completed_fields": completed,
            "required_fields": len(config["fields"]),
            "missing_fields": missing,
        }

    ready_count = sum(item["ready"] for item in modules.values())

    return {
        "profile_id": profile.profile_id,
        "modules": modules,
        "ready_module_count": ready_count,
        "module_count": len(modules),
        "notes": [
            "Readiness means required profile inputs are present.",
            "It is not a country-fit score.",
            "Each fit module still requires its own external evidence layer.",
        ],
    }
