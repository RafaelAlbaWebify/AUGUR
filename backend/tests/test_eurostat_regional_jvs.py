from app.ingestion.eurostat_regional_jvs import _ordered_codes


def test_ordered_codes_supports_jsonstat_index_map():
    dimension = {
        "category": {
            "index": {
                "ES11": 1,
                "ES12": 0,
            }
        }
    }

    assert _ordered_codes(dimension) == ["ES12", "ES11"]


def test_ordered_codes_supports_jsonstat_index_list():
    dimension = {
        "category": {
            "index": ["PT11", "PT16"]
        }
    }

    assert _ordered_codes(dimension) == ["PT11", "PT16"]
