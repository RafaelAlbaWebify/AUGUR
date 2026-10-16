import json
from app.services.ranking_provider_metadata import check_provider_metadata


def sample(**overrides):
    value = {"geo": "ES11", "time": "2025", "freq": "A",
             "age": "Y20-64", "sex": "T", "unit": "PC"}
    value.update(overrides)
    return json.dumps(value)


def test_exact_response_dimensions_unflagged_eligible_for_metadata_only():
    assert check_provider_metadata(sample(), None, geo_code="ES11", period=2025) == ()


def test_missing_and_invalid_fail_closed():
    assert check_provider_metadata(None, None, geo_code="ES11", period=2025) == ("missing_response_dimensions",)
    assert check_provider_metadata("{", None, geo_code="ES11", period=2025) == ("invalid_response_dimensions",)


def test_dimension_identity_year_and_quality_flag_gate():
    result = check_provider_metadata(sample(age="Y15-64", geo="PT11", time="2024"),
                                     "e", geo_code="ES11", period=2025)
    assert result == ("provider_dimension_mismatch", "provider_geo_mismatch",
                      "provider_period_mismatch", "provider_status_review_required")
