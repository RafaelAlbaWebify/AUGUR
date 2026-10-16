"""Strict checks for returned Eurostat observation metadata, not requested filters.

No absence of metadata can be treated as certified provenance.
"""
from __future__ import annotations
import json

PILOT_DIMENSIONS = {
    "freq": "A",
    "age": "Y20-64",
    "sex": "T",
    "unit": "PC",
}


def check_provider_metadata(
    response_dimensions_json: str | None,
    source_observation_status: str | None,
    *,
    geo_code: str,
    period: int,
    indicator_id: str | None = None,
) -> tuple[str, ...]:
    reasons = []
    if not response_dimensions_json:
        return ("missing_response_dimensions",)
    try:
        dimensions = json.loads(response_dimensions_json)
    except (ValueError, TypeError):
        return ("invalid_response_dimensions",)
    if not isinstance(dimensions, dict):
        return ("invalid_response_dimensions",)
    if any(str(dimensions.get(key)) != value for key, value in PILOT_DIMENSIONS.items()):
        reasons.append("provider_dimension_mismatch")
    if indicator_id == "regional_unemployment_rate" and dimensions.get("isced11") != "TOTAL":
        reasons.append("provider_education_mismatch")
    if str(dimensions.get("geo")) != geo_code:
        reasons.append("provider_geo_mismatch")
    if str(dimensions.get("time")) != str(period):
        reasons.append("provider_period_mismatch")
    # A quality flag is descriptive evidence; it must be interpreted against
    # official source rules, not silently classified as clean or rejected.
    if source_observation_status not in (None, ""):
        reasons.append("provider_status_review_required")
    return tuple(reasons)
