from app.db.analytics import indicator_series, indicator_registry
from app.engines.trend import calculate_trend


def country_trends(country_iso3: str) -> dict:
    indicators = indicator_registry()
    results = []

    for indicator in indicators:
        series = indicator_series(country_iso3, indicator["indicator_id"])
        if not series:
            continue

        trend = calculate_trend(
            [(row["period"], row["value"]) for row in series],
            indicator["higher_is_better"],
        )

        latest = series[-1]

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
                "trend": {
                    "direction": trend.direction,
                    "interpretation": trend.interpretation,
                    "confidence": trend.confidence,
                    "slope_per_year": trend.slope_per_year,
                    "pct_change_1y": trend.pct_change_1y,
                    "pct_change_3y": trend.pct_change_3y,
                    "pct_change_5y": trend.pct_change_5y,
                    "years_used": trend.years_used,
                },
            }
        )

    return {
        "country_iso3": country_iso3.upper(),
        "indicator_count": len(results),
        "indicators": results,
    }
