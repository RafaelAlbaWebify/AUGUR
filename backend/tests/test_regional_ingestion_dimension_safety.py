"""Guard against silent arbitrary JSON-stat dimension selection in regional sync."""
from app.services.regional_evidence import (
    REGIONAL_INDICATORS, _latest_regional_indicator,
)


class MultiEducationAdapter:
    def __init__(self):
        self.requested = None

    def fetch_dataset(self, dataset_id, filters):
        self.requested = filters
        return {"kind": "test"}

    def normalize(self, geo, config, payload):
        assert config["dimension_values"] == self.requested
        if "isced11" not in config["dimension_values"]:
            return [
                {"period": 2025, "value": 4.0},
                {"period": 2025, "value": 8.0},
            ]
        return [{"period": 2025, "value": 4.0}]


def test_unemployment_selects_education_total_in_normalizer():
    adapter = MultiEducationAdapter()
    cfg = next(item for item in REGIONAL_INDICATORS
               if item["indicator_id"] == "regional_unemployment_rate")
    row = _latest_regional_indicator(adapter, "ES11", cfg)
    assert row["status"] == "available"
    assert adapter.requested["isced11"] == "TOTAL"


class AmbiguousAdapter(MultiEducationAdapter):
    def normalize(self, geo, config, payload):
        return [{"period": 2025, "value": 4.0},
                {"period": 2025, "value": 8.0}]


def test_ambiguous_same_year_cohorts_fail_closed():
    cfg = next(item for item in REGIONAL_INDICATORS
               if item["indicator_id"] == "regional_employment_rate")
    row = _latest_regional_indicator(AmbiguousAdapter(), "ES11", cfg)
    assert row["status"] == "unavailable"
    assert row["reason"] == "ambiguous_provider_dimensions"
