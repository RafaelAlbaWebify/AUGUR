from __future__ import annotations

from app.db.analytics import indicator_peer_series


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
    target_rows = series_by_country.get(target, [])

    if not target_rows:
        return {
            "status": "target_missing",
            "reference_group": "countries_with_comparable_observation",
            "reference_countries": [],
            "sample_size": 0,
            "period": None,
            "rank_low_to_high": None,
            "percentile_low_to_high": None,
            "adequacy": "insufficient",
            "interpretation": "numeric_position_only",
            "note": "The target country has no observed value for this indicator.",
        }

    period_maps = {
        iso3: {
            int(row["period"]): row
            for row in rows
        }
        for iso3, rows in series_by_country.items()
    }

    candidates = []
    for period in sorted(
        {int(row["period"]) for row in target_rows},
        reverse=True,
    ):
        values = [
            (iso3, float(rows[period]["value"]))
            for iso3, rows in period_maps.items()
            if period in rows
        ]
        candidates.append((period, values))

    selected = next(
        (
            (period, values)
            for period, values in candidates
            if len(values) >= 5
        ),
        None,
    )

    if selected is None:
        selected = max(
            candidates,
            key=lambda item: (len(item[1]), item[0]),
        )

    period, values = selected
    reference_countries = sorted(iso3 for iso3, _ in values)
    rank = _average_rank(values, target)

    if rank is None:
        return {
            "status": "target_missing",
            "reference_group": "countries_with_comparable_observation",
            "reference_countries": reference_countries,
            "sample_size": len(values),
            "period": period,
            "rank_low_to_high": None,
            "percentile_low_to_high": None,
            "adequacy": "insufficient",
            "interpretation": "numeric_position_only",
            "note": "The target country is missing from the selected peer period.",
        }

    sample_size = len(values)
    percentile = (
        50.0
        if sample_size == 1
        else ((rank - 1.0) / (sample_size - 1.0)) * 100.0
    )
    adequacy = (
        "supported"
        if sample_size >= 5
        else "limited"
        if sample_size >= 2
        else "insufficient"
    )

    return {
        "status": "available",
        "reference_group": "countries_with_comparable_observation",
        "reference_countries": reference_countries,
        "sample_size": sample_size,
        "period": period,
        "rank_low_to_high": rank,
        "percentile_low_to_high": percentile,
        "adequacy": adequacy,
        "interpretation": "numeric_position_only",
        "note": (
            "Peer position is descriptive and does not imply better or worse. "
            "AUGUR prefers the latest target-country period with at least five "
            "comparable country observations; smaller samples are labelled limited."
        ),
    }


def indicator_peer_reference(
    indicator_id: str,
    target_country_iso3: str,
) -> dict:
    return build_peer_reference(
        indicator_id,
        target_country_iso3,
        indicator_peer_series(indicator_id),
    )
