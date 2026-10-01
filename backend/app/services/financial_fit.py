from __future__ import annotations

from app.db.analytics import latest_observations
from app.models.profile import PersonalProfileResponse


PRICE_LEVEL_INDICATOR = "household_price_level_index"


def _latest_price_level(country_iso3: str) -> dict | None:
    for row in latest_observations(country_iso3):
        if row["indicator_id"] == PRICE_LEVEL_INDICATOR:
            return row
    return None


def financial_fit(
    profile: PersonalProfileResponse,
    target_country_iso3: str,
) -> dict:
    target = target_country_iso3.upper()

    if not profile.current_country:
        return {
            "target_country_iso3": target,
            "status": "insufficient_profile",
            "reason": "current_country_missing",
            "portable_income_analysis": None,
            "notes": [
                "FinancialFit does not infer a current country.",
                "No score is produced.",
            ],
        }

    if profile.monthly_net_income is None:
        return {
            "target_country_iso3": target,
            "status": "insufficient_profile",
            "reason": "monthly_net_income_missing",
            "portable_income_analysis": None,
            "notes": [
                "Monthly net income is required for purchasing-power analysis.",
                "No score is produced.",
            ],
        }

    if not profile.remote_work:
        return {
            "target_country_iso3": target,
            "status": "local_income_unknown",
            "reason": "portable_income_not_confirmed",
            "portable_income_analysis": None,
            "notes": [
                "AUGUR will not assume current income survives relocation.",
                "Career/salary evidence is required before local-employment viability can be estimated.",
                "No score is produced.",
            ],
        }

    origin = profile.current_country.upper()
    origin_price = _latest_price_level(origin)
    target_price = _latest_price_level(target)

    if origin_price is None or target_price is None:
        return {
            "target_country_iso3": target,
            "status": "insufficient_country_evidence",
            "reason": "household_price_level_index_missing",
            "portable_income_analysis": None,
            "notes": [
                "Eurostat household price-level evidence is required for both origin and target.",
                "No score is produced.",
            ],
        }

    cost_factor = target_price["value"] / origin_price["value"]
    purchasing_power_equivalent = profile.monthly_net_income / cost_factor
    purchasing_power_change_pct = (
        (purchasing_power_equivalent / profile.monthly_net_income) - 1.0
    ) * 100

    return {
        "target_country_iso3": target,
        "status": "portable_income_comparable",
        "reason": None,
        "portable_income_analysis": {
            "origin_country_iso3": origin,
            "monthly_net_income": profile.monthly_net_income,
            "origin_price_level_index": origin_price["value"],
            "origin_period": origin_price["period"],
            "target_price_level_index": target_price["value"],
            "target_period": target_price["period"],
            "relative_cost_factor": cost_factor,
            "origin_equivalent_purchasing_power": purchasing_power_equivalent,
            "purchasing_power_change_pct": purchasing_power_change_pct,
            "source_id": target_price["source_id"],
        },
        "notes": [
            "This is a relative purchasing-power comparison, not a household budget.",
            "The calculation assumes current net income is portable because remote_work is true.",
            "Price-level indices are not adjusted for individual spending patterns.",
            "No country ranking or composite score is produced.",
        ],
    }
