from app.ingestion.eurostat import EurostatAdapter


def test_eurostat_normalization_uses_requested_country():
    payload = {
        "id": ["geo", "time"],
        "size": [1, 2],
        "dimension": {
            "geo": {
                "category": {
                    "index": {"PT": 0},
                }
            },
            "time": {
                "category": {
                    "index": {"2023": 0, "2024": 1},
                }
            },
        },
        "value": [10.4, 10.6],
        "updated": "2026-09-01",
    }

    config = {
        "indicator_id": "population_total",
        "dataset_id": "synthetic",
        "filters": {"geo": "__GEO__"},
        "unit": "persons",
    }

    adapter = EurostatAdapter(client=None)
    try:
        rows = adapter.normalize("PRT", config, payload)
    finally:
        adapter.close()

    assert len(rows) == 2
    assert {row["country_iso3"] for row in rows} == {"PRT"}
    assert rows[-1]["period"] == 2024
