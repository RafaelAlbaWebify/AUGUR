"""Grounded housing affordability evidence; never convert PPS to nominal rent ratios."""
from __future__ import annotations

OVERBURDEN = "regional_housing_cost_overburden_rate"
INCOME = "regional_disposable_income_pps_per_capita"


def housing_affordability_evidence(indicators: list[dict]) -> dict:
    by_id = {item.get("indicator_id"): item for item in indicators}
    o = by_id.get(OVERBURDEN)
    i = by_id.get(INCOME)
    available_overburden = bool(o and o.get("status") == "available" and
                                o.get("unit") == "percent" and
                                isinstance(o.get("value"), (int, float)) and
                                0 <= o["value"] <= 100)
    available_income = bool(i and i.get("status") == "available" and
                            i.get("unit") == "pps_per_person" and
                            isinstance(i.get("value"), (int, float)) and
                            i["value"] >= 0)
    return {
        "scope": "regional_official_housing_context_not_market_rent_affordability",
        "status": "partial" if available_overburden or available_income else "unavailable",
        "housing_cost_overburden": {
            "status": "available" if available_overburden else "unavailable",
            "value_pct": o["value"] if available_overburden else None,
            "period": o.get("period") if available_overburden else None,
            "source_id": o.get("source_id") if available_overburden else None,
            "dataset_id": o.get("dataset_id") if available_overburden else None,
        },
        "disposable_income_pps_per_capita": {
            "status": "available" if available_income else "unavailable",
            "value_pps": i["value"] if available_income else None,
            "period": i.get("period") if available_income else None,
            "source_id": i.get("source_id") if available_income else None,
            "dataset_id": i.get("dataset_id") if available_income else None,
        },
        "monthly_market_rent": None,
        "rent_to_net_income_pct": None,
        "affordability_complete": False,
        "limitations": [
            "Eurostat housing cost overburden is a survey-defined proportion of people; it is not average rent or the share of salary paid by an individual.",
            "Regional disposable income in PPS per inhabitant is not an individual net wage, monthly household cash income or rent denominator.",
            "Market rent, purchase prices and comparable disposable household cash income require separate official observations at matched geography and time.",
        ],
    }
