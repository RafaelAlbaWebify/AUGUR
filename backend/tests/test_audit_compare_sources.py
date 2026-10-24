"""Batch source audit regression: safe classifications, mutation and isolation."""
from scripts.audit_compare_sources import audit, audit_eurostat


def row(provider="EUROSTAT", dataset="tessi163", value=7.2):
    return dict(country_iso3="ESP", indicator_id="housing_cost_overburden_rate",
                source_id=provider, dataset_id=dataset, period=2025,
                value=value, unit="percent", source_decimal=None)


def test_parallel_report_preserves_all_rows_and_marks_unimplemented_sources():
    result = audit([row(), {**row(provider="OECD"), "country_iso3": "IRL"}],
                   check_eurostat=lambda record: {
                       "country": record["country_iso3"], "indicator_id": record["indicator_id"],
                       "status": "match"}, workers=2)
    assert result["rows"] == 2
    assert result["status_counts"] == {"match": 1, "provider_not_implemented": 1}


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
