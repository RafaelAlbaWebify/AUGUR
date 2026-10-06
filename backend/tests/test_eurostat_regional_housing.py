from app.ingestion.eurostat_regional_housing import _ordered_codes


def test_ordered_codes_supports_jsonstat_map():
    dimension = {
        "category": {
            "index": {
                "ES12": 1,
                "ES11": 0,
            }
        }
    }

    assert _ordered_codes(dimension) == ["ES11", "ES12"]


def test_ordered_codes_supports_jsonstat_list():
    dimension = {
        "category": {
            "index": ["IE04", "IE05"]
        }
    }

    assert _ordered_codes(dimension) == ["IE04", "IE05"]


from app.ingestion.eurostat_regional_housing import REGIONAL_HOUSING_SERIES


def test_housing_series_use_verified_filters():
    income = next(
        item for item in REGIONAL_HOUSING_SERIES
        if item["indicator_id"] == "regional_disposable_income_pps_per_capita"
    )
    housing = next(
        item for item in REGIONAL_HOUSING_SERIES
        if item["indicator_id"] == "regional_housing_cost_overburden_rate"
    )

    assert income["filters"]["unit"] == "PPS_EU27_2020_HAB"
    assert income["filters"]["direct"] == "BAL"
    assert income["filters"]["na_item"] == "B6N"
    assert housing["filters"]["unit"] == "PC"
    assert income["filters"]["geoLevel"] == "nuts2"
    assert housing["filters"]["geoLevel"] == "nuts2"
