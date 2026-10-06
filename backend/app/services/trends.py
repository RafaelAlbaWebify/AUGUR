from app.db.analytics import indicator_series, indicator_registry
from app.catalog import (
    INDICATORS,
    MATERIAL_CHANGE_RULES,
    MATERIAL_CHANGE_RULE_VERSION,
)
from app.engines.trend import calculate_trend
from app.services.peer_reference import indicator_peer_reference


def country_trends(country_iso3: str) -> dict:
    indicators = indicator_registry()
    catalog_by_id = {item['indicator_id']: item for item in INDICATORS}
    results = []

    for indicator in indicators:
        series = indicator_series(country_iso3, indicator["indicator_id"])
        if not series:
            continue

        catalog_item = catalog_by_id.get(indicator["indicator_id"], {})
        material_rule = MATERIAL_CHANGE_RULES.get(
            indicator["indicator_id"],
            {"mode": "relative_pct", "threshold": 1.0},
        )

        trend = calculate_trend(
            [(row["period"], row["value"]) for row in series],
            indicator["interpretation_policy"],
            indicator.get("target_min"),
            indicator.get("target_max"),
            material_rule["mode"],
            material_rule["threshold"],
        )

        latest = series[-1]
        peer_reference = indicator_peer_reference(
            indicator["indicator_id"],
            country_iso3,
        )

        results.append(
            {
                "country_iso3": country_iso3.upper(),
                "indicator_id": indicator["indicator_id"],
                "name": indicator["name"],
                "dimension": indicator["dimension"],
                "period": latest["period"],
                "value": latest["value"],
                "unit": indicator["unit"],
                "source_id": latest["source_id"],
                "interpretation_policy": indicator["interpretation_policy"],
                "target_min": indicator.get("target_min"),
                "target_max": indicator.get("target_max"),
                "methodology_note": catalog_item.get("methodology_note"),
                "comparability_note": catalog_item.get("comparability_note"),
                "peer_reference": peer_reference,
                "material_change_rule": {
                    "version": MATERIAL_CHANGE_RULE_VERSION,
                    "mode": trend.material_change_mode,
                    "threshold": trend.material_change_threshold,
                    "basis": "explicit_augur_heuristic_not_statistical_significance",
                },
                "trend": {
                    "direction": trend.direction,
                    "interpretation": trend.interpretation,
                    "confidence": trend.confidence,
                    "evidence_depth": trend.evidence_depth,
                    "trend_certainty": trend.trend_certainty,
                    "linear_fit_r2": trend.linear_fit_r2,
                    "material_change_value": trend.material_change_value,
                    "slope_per_year": trend.slope_per_year,
                    "pct_change_1y": trend.pct_change_1y,
                    "pct_change_3y": trend.pct_change_3y,
                    "pct_change_5y": trend.pct_change_5y,
                    "years_used": trend.years_used,
                    "target_status": trend.target_status,
                },
            }
        )

    return {
        "country_iso3": country_iso3.upper(),
        "indicator_count": len(results),
        "indicators": results,
    }
