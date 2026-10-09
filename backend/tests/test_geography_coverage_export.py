import csv
import json

import pytest

from scripts import export_geography_coverage as module


@pytest.fixture
def observed_response():
    return {
        "denominator": "registered_geographies",
        "indicator_count": 1,
        "groups_without_observations": [],
        "items": [{
            "country_iso3": "ESP",
            "geography_system": "OECD_TL_2024",
            "geo_level": "tl2",
            "indicator_id": "regional_population",
            "registered_geographies": 3,
            "covered_geographies": 2,
            "missing_geographies": 1,
            "coverage_ratio": 2/3,
            "oldest_latest_period": 2021,
            "newest_latest_period": 2023,
            "earliest_ingestion_by_geography": "2026-10-02T00:00:00",
            "most_recent_ingestion": "2026-10-03T00:00:00",
            "same_period_coverage": [
                {"period": 2023, "geography_count": 1, "coverage_ratio": 1/3},
            ],
            "latest_period_distribution": [
                {"period": 2023, "geography_count": 1},
            ],
        }],
    }


def test_json_export_preserves_observed_evidence(tmp_path, monkeypatch, observed_response):
    seen = {}
    def fake_coverage(**kwargs):
        seen.update(kwargs)
        return observed_response
    monkeypatch.setattr(module, "indicator_geography_coverage", fake_coverage)
    output = tmp_path / "exports" / "coverage.json"
    module.export_coverage(output=output, country="ESP", system="OECD_TL_2024", level="tl2")
    assert json.loads(output.read_text(encoding="utf-8")) == observed_response
    assert seen == {
        "country_iso3": "ESP",
        "geography_system": "OECD_TL_2024",
        "geo_level": "tl2",
    }


def test_csv_export_keeps_observation_periods(tmp_path, monkeypatch, observed_response):
    monkeypatch.setattr(module, "indicator_geography_coverage", lambda **kwargs: observed_response)
    output = tmp_path / "coverage.csv"
    module.export_coverage(output=output)
    with output.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 1
    assert rows[0]["indicator_id"] == "regional_population"
    assert json.loads(rows[0]["same_period_coverage"])[0]["period"] == 2023


def test_export_refuses_unsupported_file_type_without_writing(tmp_path, monkeypatch, observed_response):
    monkeypatch.setattr(module, "indicator_geography_coverage", lambda **kwargs: observed_response)
    output = tmp_path / "coverage.txt"
    with pytest.raises(ValueError, match="Only .json and .csv"):
        module.export_coverage(output=output)
    assert not output.exists()
