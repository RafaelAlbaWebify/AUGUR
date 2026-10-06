from app.ingestion.eurostat import EurostatAdapter
from app.ingestion.eurostat_regional_labour import normalize_subnational


def test_normalize_subnational_keeps_target_nuts2_regions_only():
    payload = {
        "id": ["geo", "time"],
        "size": [4, 1],
        "dimension": {
            "geo": {
                "category": {
                    "index": {
                        "ES11": 0,
                        "ES12": 1,
                        "PT11": 2,
                        "BG31": 3,
                    },
                    "label": {
                        "ES11": "Galicia",
                        "ES12": "Principado de Asturias",
                        "PT11": "Norte",
                        "BG31": "Severozapaden",
                    },
                }
            },
            "time": {
                "category": {
                    "index": {
                        "2025": 0,
                    }
                }
            },
        },
        "value": [70.0, 72.0, 74.0, 68.0],
        "updated": "2026-09-10",
    }
    config = {
        "indicator_id": "regional_employment_rate",
        "dataset_id": "lfst_r_lfe2emprt",
        "unit": "percent",
    }

    adapter = EurostatAdapter(client=None)
    try:
        rows = normalize_subnational(adapter, config, payload)
    finally:
        adapter.close()

    assert [row["geo_code"] for row in rows] == ["ES11", "ES12", "PT11"]
    assert rows[0]["geo_name"] == "Galicia"
    assert rows[1]["geo_name"] == "Principado de Asturias"
    assert all(row["geo_level"] == "NUTS2" for row in rows)


def test_normalize_subnational_rejects_non_nuts2_codes():
    payload = {
        "id": ["geo", "time"],
        "size": [3, 1],
        "dimension": {
            "geo": {
                "category": {
                    "index": {
                        "ES": 0,
                        "ES1": 1,
                        "ES11": 2,
                    },
                    "label": {
                        "ES": "Spain",
                        "ES1": "Noroeste",
                        "ES11": "Galicia",
                    },
                }
            },
            "time": {
                "category": {
                    "index": {
                        "2025": 0,
                    }
                }
            },
        },
        "value": [65.0, 66.0, 67.0],
        "updated": "2026-09-10",
    }
    config = {
        "indicator_id": "regional_unemployment_rate",
        "dataset_id": "lfst_r_lfu3rt",
        "unit": "percent",
    }

    adapter = EurostatAdapter(client=None)
    try:
        rows = normalize_subnational(adapter, config, payload)
    finally:
        adapter.close()

    assert [row["geo_code"] for row in rows] == ["ES11"]
