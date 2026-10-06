from app.ingestion.eurostat_regional_health import _ordered_codes


def test_ordered_codes_supports_map():
    dimension = {"category": {"index": {"ES12": 1, "ES11": 0}}}
    assert _ordered_codes(dimension) == ["ES11", "ES12"]


def test_ordered_codes_supports_list():
    dimension = {"category": {"index": ["IE04", "IE05"]}}
    assert _ordered_codes(dimension) == ["IE04", "IE05"]


from app.ingestion.eurostat_regional_health import REGIONAL_HEALTH_SERIES


def test_health_series_use_verified_filters():
    unmet = next(
        item for item in REGIONAL_HEALTH_SERIES
        if item["indicator_id"] == "regional_unmet_medical_needs"
    )
    beds = next(
        item for item in REGIONAL_HEALTH_SERIES
        if item["indicator_id"] == "regional_hospital_beds_per_100k"
    )

    assert unmet["filters"]["reason"] == "TXP_TFAR_WLIST"
    assert unmet["filters"]["unit"] == "PC"
    assert beds["filters"]["unit"] == "P_HTHAB"
    assert unmet["filters"]["geoLevel"] == "nuts2"
    assert beds["filters"]["geoLevel"] == "nuts2"
