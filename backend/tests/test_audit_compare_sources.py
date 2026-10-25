"""Batch source audit regression: safe classifications, mutation and isolation."""
from scripts.audit_compare_sources import audit, audit_eurostat


def row(provider="EUROSTAT", dataset="tessi163", value=7.2):
    return dict(country_iso3="ESP", indicator_id="housing_cost_overburden_rate",
                source_id=provider, dataset_id=dataset, period=2025,
                value=value, unit="percent", source_decimal=None)


def test_parallel_report_marks_bad_other_source_contract():
    result = audit([row(), {**row(provider="OECD"), "country_iso3": "IRL"}],
                   check_eurostat=lambda record: {
                       "country": record["country_iso3"], "indicator_id": record["indicator_id"],
                       "status": "match"}, workers=2)
    assert result["rows"] == 2
    assert result["status_counts"] == {"match": 1, "source_drift": 1}


def test_mismatched_persisted_dataset_never_fetches():
    class NoFetch:
        def __init__(self):
            raise AssertionError("Unexpected source request")
    result = audit_eurostat(row(dataset="wrong_version"), adapter_factory=NoFetch)
    assert result["status"] == "source_drift"


def test_exact_source_value_and_value_drift_with_stub():
    class Fake:
        def fetch_dataset(self, dataset_id, filters):
            assert dataset_id == "tessi163"
            assert filters["geo"] == "ES"
            assert filters["sinceTimePeriod"] == "2025"
            return {"stub": True}
        def normalize(self, country, config, payload):
            return [{"period": 2025, "value": 7.2, "source_updated_at": "2026-10",
                     "source_dimensions": {"geo": "ES"}}]
        def close(self):
            pass
    assert audit_eurostat(row(), adapter_factory=Fake)["status"] == "match"
    assert audit_eurostat(row(value=9.2), adapter_factory=Fake)["status"] == "value_drift"


def test_duplicate_country_indicator_fails_closed():
    import pytest
    with pytest.raises(ValueError, match="Duplicate"):
        audit([row(), row()])


def test_provider_comparison_detects_change_and_type_mismatch():
    from scripts.audit_compare_sources import classify_observation
    stored = {"unit": "percent", "dataset_id": "WDI", "value": 4.0,
              "observation_type": "observed"}
    base = {"country": "ESP", "indicator_id": "x"}
    current = {**stored, "value": 4.5}
    assert classify_observation(base, stored, [current])["status"] == "value_drift"
    assert classify_observation(base, stored, [{**current, "observation_type": "official_forecast"}])["status"] == "observation_type_drift"
    assert classify_observation(base, stored, [{**current, "unit": "persons"}])["status"] == "source_drift"


def test_imf_archived_vintage_never_silently_passes():
    from scripts.audit_compare_sources import audit_provider
    item = row(provider="IMF", dataset="WEO_APRIL_2026")
    result = audit_provider(item)
    assert result["status"] == "vintage_unverifiable"
