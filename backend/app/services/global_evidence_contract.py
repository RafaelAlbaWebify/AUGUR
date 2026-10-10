"""Country-agnostic evidence contract for expanding AUGUR beyond pilot nations.

Describes comparable data; never assumes a country, region or city has observations.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


Level = Literal["country", "region", "city", "fua"]


@dataclass(frozen=True)
class EvidenceContract:
    indicator_id: str
    unit: str
    levels: tuple[Level, ...]
    source_id: str
    dataset_id: str
    geography_system: str | None = None
    minimum_period: int | None = None


def validate_observation(contract: EvidenceContract, record: dict) -> list[str]:
    """Return explicit incompatibilities; never coerce or impute observations."""
    problems = []
    if record.get("indicator_id") != contract.indicator_id:
        problems.append("indicator_mismatch")
    if record.get("unit") != contract.unit:
        problems.append("unit_mismatch")
    if record.get("source_id") != contract.source_id or record.get("dataset_id") != contract.dataset_id:
        problems.append("source_mismatch")
    if record.get("geo_level") not in contract.levels:
        problems.append("level_mismatch")
    if contract.geography_system and record.get("geography_system") != contract.geography_system:
        problems.append("geography_system_mismatch")
    period = record.get("period")
    if not isinstance(period, int) or isinstance(period, bool) or (
        contract.minimum_period is not None and period < contract.minimum_period
    ):
        problems.append("period_invalid")
    value = record.get("value")
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        problems.append("value_invalid")
    else:
        from math import isfinite
        if not isfinite(value):
            problems.append("value_invalid")
    if not record.get("geo_code"):
        problems.append("geography_missing")
    return problems


def coverage_matrix(contracts: list[EvidenceContract], observations: list[dict], geographies: list[dict]) -> list[dict]:
    """All combinations are explicit; 'missing' is never zero.

    Geographies are provider/code/level memberships. Observations are joined on
    geography system, geo code and level; data from a country is not inherited
    by a city. No assumed globally complete geographical universe.
    """
    result = []
    for geo in geographies:
        for contract in contracts:
            if geo.get("geo_level") not in contract.levels:
                continue
            if contract.geography_system and geo.get("geography_system") != contract.geography_system:
                continue
            candidates = [
                row for row in observations
                if row.get("geo_code") == geo.get("geo_code")
                and row.get("geo_level") == geo.get("geo_level")
                and row.get("geography_system") == geo.get("geography_system")
                and row.get("indicator_id") == contract.indicator_id
            ]
            accepted = [row for row in candidates if not validate_observation(contract, row)]
            result.append({
                "country_iso3": geo.get("country_iso3"),
                "geo_code": geo.get("geo_code"),
                "geo_level": geo.get("geo_level"),
                "geography_system": geo.get("geography_system"),
                "indicator_id": contract.indicator_id,
                "status": "observed" if accepted else "incompatible" if candidates else "missing",
                "periods": sorted({row["period"] for row in accepted}),
                "rejected_reasons": sorted({
                    reason for row in candidates for reason in validate_observation(contract, row)
                }),
            })
    return result
