from app.services.city_evidence import city_evidence


class FakeAdapter:
    def fetch_dataset(self, dataset_id, filters):
        assert dataset_id == "urb_cpop1"
        assert filters["cities"] == "ES001C"
        assert filters["indic_ur"] == "DE1001V"
        return {"ok": True}

    def normalize(self, city_code, config, payload):
        assert city_code == "ES001C"
        return [
            {
                "period": 2024,
                "value": 3200000.0,
                "source_updated_at": "2026-10-02",
            },
            {
                "period": 2025,
                "value": 3250000.0,
                "source_updated_at": "2026-10-02",
            },
        ]


def test_city_evidence_returns_latest_population():
    result = city_evidence("ES001C", adapter=FakeAdapter())

    assert result["city_code"] == "ES001C"
    assert result["geo_level"] == "city"
    assert result["minimum_population_scope"] == 50000
    assert result["available_count"] == 1
    assert result["indicators"][0]["period"] == 2025
    assert result["indicators"][0]["value"] == 3250000.0
