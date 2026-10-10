import pytest
from app.ingestion import oecd_regional as module


def test_oecd_guard_accepts_non_eu_valid_sourced_rows():
    module._validate_oecd_rows_before_write([{
        "geo_code": "AU1", "country_iso3": "AUS",
        "geo_level": "tl2", "geography_system": "OECD_TL_2024",
        "indicator_id": "regional_population", "unit": "persons",
        "source_id": "OECD", "dataset_id": module.POPULATION_DATASET_ID,
        "period": 2024, "value": 8100000,
    }], module.POPULATION_DATASET_ID)


@pytest.mark.parametrize("changed,reason", [
    ({"geography_system": "NUTS_2024"}, "geography_system_mismatch"),
    ({"dataset_id": "wrong"}, "source_mismatch"),
    ({"value": float("nan")}, "value_invalid"),
    ({"country_iso3": None}, "country_missing"),
])
def test_oecd_guard_rejects_incompatible_rows(changed, reason):
    row = {
        "geo_code": "AU1", "country_iso3": "AUS",
        "geo_level": "tl2", "geography_system": "OECD_TL_2024",
        "indicator_id": "regional_population", "unit": "persons",
        "source_id": "OECD", "dataset_id": module.POPULATION_DATASET_ID,
        "period": 2024, "value": 8100000,
    }
    row.update(changed)
    with pytest.raises(ValueError, match=reason):
        module._validate_oecd_rows_before_write([row], module.POPULATION_DATASET_ID)
