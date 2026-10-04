from app.services.regional_evidence import (
    REGIONAL_INDICATORS,
    geographic_level,
    regional_comparison,
    regional_evidence,
)


class FakeAdapter:
    def fetch_dataset(self, dataset_id, filters):
        return {
            "dataset_id": dataset_id,
            "geo": filters["geo"],
        }

    def normalize(self, geo_code, config, payload):
        base = float(len(config["indicator_id"]))
        return [
            {
                "period": 2023,
                "value": base,
                "source_updated_at": "2026-01-01",
            },
            {
                "period": 2024,
                "value": base + 1,
                "source_updated_at": "2026-09-01",
            },
        ]


def test_geographic_level_recognises_nuts2_and_nuts3():
    assert geographic_level("ES11") == "nuts2"
    assert geographic_level("ES111") == "nuts3"
    assert geographic_level("ES") == "unknown"


def test_regional_evidence_returns_latest_available_values():
    result = regional_evidence("ES11", adapter=FakeAdapter())

    assert result["geo_code"] == "ES11"
    assert result["geo_level"] == "nuts2"
    assert result["indicator_count"] == len(REGIONAL_INDICATORS)
    assert result["available_count"] == len(REGIONAL_INDICATORS)
    assert result["complete"] is True
    assert {item["period"] for item in result["indicators"]} == {2024}
    assert {item["source_id"] for item in result["indicators"]} == {"EUROSTAT"}


def test_regional_comparison_keeps_region_codes_separate():
    result = regional_comparison(
        ["ES11", "PT11"],
        adapter=FakeAdapter(),
    )

    assert result["regions"] == [
        {"geo_code": "ES11", "geo_level": "nuts2"},
        {"geo_code": "PT11", "geo_level": "nuts2"},
    ]
    assert result["indicator_count"] == len(REGIONAL_INDICATORS)
    for indicator in result["indicators"]:
        assert set(indicator["regions"]) == {"ES11", "PT11"}
