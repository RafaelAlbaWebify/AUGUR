from __future__ import annotations

from app.db.analytics import latest_labour_earnings, latest_observations
from app.services.career_fit import resolve_esco_occupation
from app.models.profile import PersonalProfileResponse


PRICE_LEVEL_INDICATOR = "household_price_level_index"


def _latest_price_level(country_iso3: str) -> dict | None:
    for row in latest_observations(country_iso3):
        if row["indicator_id"] == PRICE_LEVEL_INDICATOR:
            return row
    return None


def _local_income_reference(
    profile: PersonalProfileResponse,
    target_country_iso3: str,
) -> dict | None:
    occupation_match = resolve_esco_occupation(profile.profession)
    selected = occupation_match.get("selected")
    if not selected:
        return None

    isco_group = str(selected.get("isco_group") or "")
    if not isco_group or not isco_group[0].isdigit():
        return None

    ses_group = f"OC{isco_group[0]}"
    rows = latest_labour_earnings(target_country_iso3, ses_group)
    if not rows:
        return None

    row = rows[0]
    return {
        "occupation_label": selected["preferred_label"],
        "occupation_match_score": selected["match_score"],
        "isco_group": isco_group,
        "ses_isco_major_group": ses_group,
        "gross_monthly_mean_eur": row["value"],
        "period": row["period"],
        "source_id": row["source_id"],
        "dataset_id": row["dataset_id"],
        "source_updated_at": row.get("source_updated_at"),
    }


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
        local_income_reference = _local_income_reference(profile, target)

        if local_income_reference is None:
            return {
                "target_country_iso3": target,
                "status": "local_income_unknown",
                "reason": "local_earnings_evidence_missing",
                "portable_income_analysis": None,
                "local_income_reference": None,
                "notes": [
                    "AUGUR will not assume current income survives relocation.",
                    "No sufficiently matched Eurostat SES occupation earnings reference is available.",
                    "No score is produced.",
                ],
            }

        return {
            "target_country_iso3": target,
            "status": "local_income_reference_available",
            "reason": "net_income_not_modelled",
            "portable_income_analysis": None,
            "local_income_reference": local_income_reference,
            "notes": [
                "Eurostat SES provides a structural gross monthly earnings reference, not a job offer or current salary quote.",
                "The reference is a mean for a broad ISCO-08 major group and enterprises with 10 or more employees.",
                "Net pay, taxes, household budget and location-specific salary variation are not yet modelled.",
                "This evidence remains partial and does not unlock TTV.",
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
        "local_income_reference": None,
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
