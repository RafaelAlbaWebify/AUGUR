from app.ingestion.eurostat_regional_access_safety import _ordered_codes


def test_ordered_codes_accepts_jsonstat_map():
    assert _ordered_codes({
        "category": {
            "index": {
                "ES12": 1,
                "ES11": 0,
            }
        }
    }) == ["ES11", "ES12"]


def test_ordered_codes_accepts_jsonstat_list():
    assert _ordered_codes({
        "category": {
            "index": ["IE041", "IE042"]
        }
    }) == ["IE041", "IE042"]
