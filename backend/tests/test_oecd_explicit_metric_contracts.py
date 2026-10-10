import pytest
from app.ingestion.oecd_regional import (
    _validate_oecd_rows_before_write,
    OECD_REGIONAL_ALLOWED_METRICS,
    POPULATION_DATASET_ID,
    LABOUR_DATASET_ID,
)

def _row():
    return {
        "geo_code": "AU1", "country_iso3": "AUS", "geo_level": "tl2",
        "geography_system": "OECD_TL_2024",
        "indicator_id": "regional_population", "unit": "persons",
        "source_id": "OECD", "dataset_id": POPULATION_DATASET_ID,
        "period": 2024, "value": 10,
    }

def test_verified_dataset_accepts_non_eu_country():
    _validate_oecd_rows_before_write([_row()], POPULATION_DATASET_ID)

def test_unknown_metric_rejected_even_when_self_described_unit_matches():
    row = _row()
    row["indicator_id"] = "invented_oecd_metric"
    with pytest.raises(ValueError, match="indicator not registered"):
        _validate_oecd_rows_before_write([row], POPULATION_DATASET_ID)

def test_wrong_unit_rejected_from_known_dataset():
    row = _row()
    row["unit"] = "thousands_of_persons"
    with pytest.raises(ValueError, match="unit_mismatch"):
        _validate_oecd_rows_before_write([row], POPULATION_DATASET_ID)

def test_cross_dataset_metric_rejected():
    row = _row()
    row["dataset_id"] = LABOUR_DATASET_ID
    with pytest.raises(ValueError, match="indicator not registered"):
        _validate_oecd_rows_before_write([row], LABOUR_DATASET_ID)

def test_unknown_dataset_rejected_with_empty_batch():
    with pytest.raises(ValueError, match="dataset not registered"):
        _validate_oecd_rows_before_write([], "UNKNOWN")

def test_every_registered_dataset_has_at_least_one_metric():
    assert len(OECD_REGIONAL_ALLOWED_METRICS) == 9
    assert all(metrics for metrics in OECD_REGIONAL_ALLOWED_METRICS.values())
