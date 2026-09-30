from collections import defaultdict

from app.engines.dimension import summarize_dimension
from app.services.trends import country_trends


def country_assessment(country_iso3: str) -> dict:
    trends = country_trends(country_iso3)

    grouped: dict[str, list[dict]] = defaultdict(list)
    for indicator in trends["indicators"]:
        grouped[indicator["dimension"]].append(indicator)

    dimensions = {
        dimension: summarize_dimension(indicators)
        for dimension, indicators in grouped.items()
    }

    return {
        "country_iso3": country_iso3.upper(),
        "method": "transparent_signal_synthesis_v1",
        "dimensions": dimensions,
    }
