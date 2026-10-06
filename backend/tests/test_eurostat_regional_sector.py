from app.ingestion.eurostat import EurostatAdapter
from app.ingestion.eurostat_regional_sector import (
    normalize_regional_sector_employment,
)


def test_normalize_regional_sector_keeps_target_regions_and_single_nace_sections():
    payload = {
        "id": ["geo", "nace_r2", "time"],
        "size": [3, 4, 1],
        "dimension": {
            "geo": {
                "category": {
                    "index": {
                        "ES11": 0,
                        "ES12": 1,
                        "BG31": 2,
                    },
                    "label": {
                        "ES11": "Galicia",
                        "ES12": "Principado de Asturias",
                        "BG31": "Severozapaden",
                    },
                }
            },
            "nace_r2": {
                "category": {
                    "index": {
                        "TOTAL": 0,
                        "C": 1,
                        "J": 2,
                        "B-E": 3,
                    },
                    "label": {
                        "TOTAL": "Total",
                        "C": "Manufacturing",
                        "J": "Information and communication",
                        "B-E": "Industry",
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
        "value": [
            1000.0, 150.0, 50.0, 220.0,
            500.0, 70.0, 20.0, 110.0,
            800.0, 120.0, 30.0, 180.0,
        ],
        "updated": "2026-09-10",
    }

    adapter = EurostatAdapter(client=None)
    try:
        rows = normalize_regional_sector_employment(adapter, payload)
    finally:
        adapter.close()

    assert {row["geo_code"] for row in rows} == {"ES11", "ES12"}
    assert {row["nace_code"] for row in rows} == {"TOTAL", "C", "J"}
    assert all(row["geo_level"] == "NUTS2" for row in rows)
    assert all(row["dataset_id"] == "lfst_r_lfe2en2" for row in rows)


def test_normalize_regional_sector_preserves_region_and_sector_labels():
    payload = {
        "id": ["geo", "nace_r2", "time"],
        "size": [1, 1, 1],
        "dimension": {
            "geo": {
                "category": {
                    "index": {"ES12": 0},
                    "label": {"ES12": "Principado de Asturias"},
                }
            },
            "nace_r2": {
                "category": {
                    "index": {"J": 0},
                    "label": {"J": "Information and communication"},
                }
            },
            "time": {
                "category": {
                    "index": {"2025": 0}
                }
            },
        },
        "value": [18.4],
        "updated": "2026-09-10",
    }

    adapter = EurostatAdapter(client=None)
    try:
        rows = normalize_regional_sector_employment(adapter, payload)
    finally:
        adapter.close()

    assert len(rows) == 1
    assert rows[0]["geo_name"] == "Principado de Asturias"
    assert rows[0]["nace_label"] == "Information and communication"
    assert rows[0]["employment_thousands"] == 18.4
