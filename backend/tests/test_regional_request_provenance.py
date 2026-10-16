"""Verify requested Eurostat dimensions are retained alongside new evidence."""
import json
from app.services.regional_evidence import (
    REGIONAL_INDICATORS, _latest_regional_indicator,
)


class AdapterStub:
    def __init__(self):
        self.filters = None

    def fetch_dataset(self, dataset_id, filters):
        self.filters = dict(filters)
        return {"updated": "2026-09-10"}

    def normalize(self, geo_code, config, payload):
        return [{"period": 2025, "value": 7.3,
                 "source_updated_at": payload["updated"]}]


def test_request_provenance_retains_exact_pilot_dimensions():
    cfg = next(x for x in REGIONAL_INDICATORS
               if x["indicator_id"] == "regional_unemployment_rate")
    adapter = AdapterStub()
    result = _latest_regional_indicator(adapter, "ES11", cfg)
    assert result["status"] == "available"
    saved = json.loads(result["request_filters_json"])
    assert saved == {"geo": "ES11", "freq": "A",
                     "age": "Y20-64", "sex": "T", "unit": "PC", "isced11": "TOTAL"}
    assert saved == adapter.filters


def test_request_provenance_is_not_false_boundary_certification():
    cfg = next(x for x in REGIONAL_INDICATORS
               if x["indicator_id"] == "regional_employment_rate")
    result = _latest_regional_indicator(AdapterStub(), "PT11", cfg)
    assert "boundary_verified" not in result
    assert "observation_status" not in result
