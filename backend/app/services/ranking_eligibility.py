"""GR-1 conservative ranking eligibility rules; no inferred source equivalence."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from math import isfinite


@dataclass(frozen=True)
class RankingContract:
    indicator_id: str
    geo_level: str
    geography_system: str
    unit: str
    source_id: str
    dataset_id: str
    period: int
    observed_only: bool = True


@dataclass(frozen=True)
class RankingCandidate:
    geo_id: str
    indicator_id: str
    geo_level: str
    geography_system: str
    unit: str
    source_id: str
    dataset_id: str
    period: int
    value: float
    observation_type: str = "observed"
    boundary_verified: bool = False


# Explicitly restricted pilot cohorts. A stored indicator is NOT automatically
# an eligible comparable construct. Source semantics/vintage still require
# independent acceptance before these can be exposed as certified rankings.
PILOT_CONTRACTS = {
    "regional_unemployment_rate": RankingContract(
        "regional_unemployment_rate", "nuts2", "NUTS_2024",
        "percent", "EUROSTAT", "lfst_r_lfu3rt", 2025
    ),
    "regional_employment_rate": RankingContract(
        "regional_employment_rate", "nuts2", "NUTS_2024",
        "percent", "EUROSTAT", "lfst_r_lfe2emprt", 2025
    ),
}


def check_eligibility(
    candidate: RankingCandidate,
    contract: RankingContract,
    *,
    today: date | None = None,
) -> tuple[str, ...]:
    """Return blocking reason codes; empty tuple means contract-eligible.

    Eligibility does not certify the provider's statistical methodology.
    'boundary_verified' must come from independent authoritative validation,
    NOT simply from a stored NUTS_2024 string.
    """
    reasons: list[str] = []
    if candidate.indicator_id != contract.indicator_id:
        reasons.append("indicator_mismatch")
    if candidate.geo_level.lower() != contract.geo_level.lower():
        reasons.append("geographic_level_mismatch")
    if candidate.geography_system != contract.geography_system:
        reasons.append("geography_system_mismatch")
    if not candidate.boundary_verified:
        reasons.append("unverified_boundary_vintage")
    if candidate.unit != contract.unit:
        reasons.append("unit_mismatch")
    if candidate.source_id != contract.source_id or candidate.dataset_id != contract.dataset_id:
        reasons.append("source_contract_mismatch")
    if candidate.period != contract.period:
        reasons.append("period_mismatch")
    if candidate.period > (today or date.today()).year:
        reasons.append("future_period")
    if contract.observed_only and candidate.observation_type != "observed":
        reasons.append("not_observed")
    if not isfinite(candidate.value):
        reasons.append("invalid_value")
    if not candidate.geo_id.strip():
        reasons.append("missing_geo_id")
    return tuple(reasons)


def ordered_eligible(
    candidates: list[RankingCandidate], contract: RankingContract, *,
    descending: bool = False, today: date | None = None,
) -> tuple[list[RankingCandidate], dict[str, int]]:
    """Stable order and auditable exclusion reasons; fail closed on duplicates."""
    accepted: list[RankingCandidate] = []
    excluded: dict[str, int] = {}
    from collections import Counter
    counts = Counter(c.geo_id for c in candidates)
    for candidate in candidates:
        reasons = list(check_eligibility(candidate, contract, today=today))
        if counts[candidate.geo_id] > 1:
            reasons.append("duplicate_geography")
        if reasons:
            for reason in reasons:
                excluded[reason] = excluded.get(reason, 0) + 1
        else:
            accepted.append(candidate)
    return (
        sorted(accepted, key=lambda c: ((-c.value if descending else c.value), c.geo_id)),
        dict(sorted(excluded.items())),
    )
