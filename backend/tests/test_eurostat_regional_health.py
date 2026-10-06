from app.ingestion.eurostat_regional_health import _ordered_codes


def test_ordered_codes_supports_map():
    dimension = {"category": {"index": {"ES12": 1, "ES11": 0}}}
    assert _ordered_codes(dimension) == ["ES11", "ES12"]


def test_ordered_codes_supports_list():
    dimension = {"category": {"index": ["IE04", "IE05"]}}
    assert _ordered_codes(dimension) == ["IE04", "IE05"]
