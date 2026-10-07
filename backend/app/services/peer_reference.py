from __future__ import annotations

from app.db.analytics import indicator_series
from app.services.country import list_countries


def _average_rank(values: list[tuple[str, float]], target_iso3: str) -> float | None:
    ordered = sorted(values, key=lambda item: (item[1], item[0]))
    target = next((value for iso3, value in ordered if iso3 == target_iso3), None)
    if target is None:
        return None

    tied_positions = [
        index + 1
        for index, (_, value) in enumerate(ordered)
        if abs(value - target) < 1e-12
    ]
    if not tied_positions:
        return None
    return sum(tied_positions) / len(tied_positions)


def build_peer_reference(
    indicator_id: str,
    target_country_iso3: str,
    series_by_country: dict[str, list[dict]],
) -> dict:
    target = target_country_iso3.upper()
    registered = sorted(series_by_country)

    period_maps: dict[str, dict[int, dict]] = {}
    for iso3 in registered:
        rows = series_by_country.get(iso3, [])
        period_maps[iso3] = {
            int(row["period"]): row
            for row in rows
        }

    common_periods = set(period_maps[registered[0]]) if registered else set()
    for iso3 in registered[1:]:
        common_periods &= set(period_maps[iso3])

    if not common_periods:
        return {
            "status": "insufficient_common_period",
            "reference_group": "registered_countries",
            "reference_countries": registered,
            "sample_size": 0,
            "period": None,
            "rank_low_to_high": None,
            "percentile_low_to_high": None,
            "adequacy": "insufficient",
            "interpretation": "numeric_position_only",
            "note": "No common observed period exists across all registered countries for this indicator.",
        }

    period = max(common_periods)
    values = [
        (iso3, float(period_maps[iso3][period]["value"]))
        for iso3 in registered
    ]

    rank = _average_rank(values, target)
    if rank is None:
        return {
            "status": "target_missing",
            "reference_group": "registered_countries",
            "reference_countries": registered,
            "sample_size": len(values),
            "period": period,
            "rank_low_to_high": None,
            "percentile_low_to_high": None,
            "adequacy": "insufficient",
            "interpretation": "numeric_position_only",
            "note": "Target country is missing from the common-period peer values.",
        }

    sample_size = len(values)
    percentile = 50.0 if sample_size == 1 else ((rank - 1.0) / (sample_size - 1.0)) * 100.0
    adequacy = "supported" if sample_size >= 5 else "limited"

    return {
        "status": "available",
        "reference_group": "registered_countries",
        "reference_countries": registered,
        "sample_size": sample_size,
        "period": period,
        "rank_low_to_high": rank,
        "percentile_low_to_high": percentile,
        "adequacy": adequacy,
        "interpretation": "numeric_position_only",
        "note": (
            "Peer position is descriptive and does not imply better or worse. "
            "With fewer than five countries, AUGUR labels the reference as limited."
        ),
    }


def indicator_peer_reference(
    indicator_id: str,
    target_country_iso3: str,
) -> dict:
    series_by_country = {
        country["iso3"]: indicator_series(country["iso3"], indicator_id)
        for country in list_countries()
        if country.get("analysis_status") == "available"
    }
    return build_peer_reference(
        indicator_id,
        target_country_iso3,
        series_by_country,
    )
