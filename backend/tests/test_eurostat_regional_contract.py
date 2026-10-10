import pytest
from app.ingestion.eurostat_regional_contract import validate_eurostat_regional_rows


def row(**changes):
    item = {"geo_code": "BG31", "geo_level": "NUTS2",
            "indicator_id": "regional_housing_cost_overburden_rate",
            "period": 2024, "value": 13.0, "unit": "percent",
            "source_id": "EUROSTAT", "dataset_id": "ilc_lvho07_r"}
    item.update(changes)
    return item


def test_non_pilot_european_region_is_supported():
    validate_eurostat_regional_rows([row()], allowed_indicators={"regional_housing_cost_overburden_rate"})


@pytest.mark.parametrize("change,message", [
    ({"unit": "pps_per_person"}, "unit_mismatch"),
    ({"dataset_id": "other"}, "source_mismatch"),
    ({"value": float("nan")}, "value_invalid"),
    ({"geo_level": "NUTS3"}, "level_mismatch"),
    ({"indicator_id": "regional_unemployment_rate"}, "Unexpected"),
])
def test_rejects_wrong_provenance_or_unexpected_indicator(change, message):
    with pytest.raises(ValueError, match=message):
        validate_eurostat_regional_rows([row(**change)], allowed_indicators={"regional_housing_cost_overburden_rate"})


def test_no_assumed_nuts_vintage():
    validate_eurostat_regional_rows([row()], allowed_indicators={"regional_housing_cost_overburden_rate"})
