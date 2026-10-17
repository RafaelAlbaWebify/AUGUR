"""Protect against reintroducing age-cohort collisions in regional indicators."""
import pytest
from app.ingestion import eurostat_regional_labour as labour


def test_regional_labour_matches_canonical_contracts():
    labour.validate_labour_indicator_contracts()
    assert {item["filters"]["age"] for item in labour.REGIONAL_LABOUR_SERIES} == {"Y20-64"}


def test_age_drift_fails_before_ingestion(monkeypatch):
    original = labour.REGIONAL_LABOUR_SERIES
    altered = [{**item, "filters": {**item["filters"]}} for item in original]
    altered[0]["filters"]["age"] = "Y15-64"
    monkeypatch.setattr(labour, "REGIONAL_LABOUR_SERIES", altered)
    with pytest.raises(ValueError, match="dimension contract mismatch"):
        labour.validate_labour_indicator_contracts()
