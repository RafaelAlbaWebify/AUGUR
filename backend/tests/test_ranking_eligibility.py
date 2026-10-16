from dataclasses import replace
from datetime import date
from math import nan

from app.services.ranking_eligibility import (
    PILOT_CONTRACTS, RankingCandidate, check_eligibility, ordered_eligible,
)

CONTRACT = PILOT_CONTRACTS["regional_unemployment_rate"]


def candidate(**overrides):
    base = RankingCandidate(
        geo_id="ESP:NUTS_2024:ES11", indicator_id=CONTRACT.indicator_id,
        geo_level=CONTRACT.geo_level, geography_system=CONTRACT.geography_system,
        unit=CONTRACT.unit, source_id=CONTRACT.source_id,
        dataset_id=CONTRACT.dataset_id, period=CONTRACT.period,
        value=7.2, boundary_verified=True,
    )
    return replace(base, **overrides)


def test_matching_observed_evidence_is_eligible():
    assert check_eligibility(candidate(), CONTRACT, today=date(2026, 10, 16)) == ()


def test_unverified_vintage_rejected_even_with_matching_system_string():
    assert "unverified_boundary_vintage" in check_eligibility(
        candidate(boundary_verified=False), CONTRACT, today=date(2026, 10, 16)
    )


def test_source_unit_level_year_and_future_projection_rejected():
    bad = candidate(
        geo_level="city", unit="thousands", source_id="OTHER",
        period=2028, observation_type="forecast", value=nan,
    )
    reasons = check_eligibility(bad, CONTRACT, today=date(2026, 10, 16))
    for reason in ("geographic_level_mismatch", "unit_mismatch",
                   "source_contract_mismatch", "period_mismatch",
                   "future_period", "not_observed", "invalid_value"):
        assert reason in reasons


def test_order_stable_and_counts_exclusions():
    a = candidate(geo_id="ES11", value=10)
    b = candidate(geo_id="PT11", value=6)
    c = candidate(geo_id="IE04", value=6)
    invalid = candidate(geo_id="IE05", boundary_verified=False)
    ordered, exclusions = ordered_eligible([a, b, invalid, c], CONTRACT, today=date(2026, 10, 16))
    assert [x.geo_id for x in ordered] == ["IE04", "PT11", "ES11"]
    assert exclusions == {"unverified_boundary_vintage": 1}
    descending, _ = ordered_eligible([a, b, c], CONTRACT, descending=True, today=date(2026, 10, 16))
    assert [x.geo_id for x in descending] == ["ES11", "IE04", "PT11"]


def test_no_implicit_semantic_or_unit_conversion():
    assert "indicator_mismatch" in check_eligibility(
        candidate(indicator_id="national_unemployment_rate"), CONTRACT, today=date(2026, 10, 16)
    )
    assert "unit_mismatch" in check_eligibility(
        candidate(unit="percentage_points"), CONTRACT, today=date(2026, 10, 16)
    )
