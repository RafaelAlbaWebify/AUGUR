"""No corrupt batch may reach an observation database write."""
import pytest
from app.db.write_contract import validate_write_batch

NATIONAL = {"country_iso3": "ESP", "indicator_id": "employment_rate", "period": 2025,
            "value": 70.0, "source_id": "EUROSTAT", "dataset_id": "test",
            "observation_type": "observed"}
REGIONAL = {"geo_code": "ES11", "geo_level": "NUTS2", "indicator_id": "regional_employment_rate",
            "period": 2025, "value": 72.5, "source_id": "EUROSTAT", "dataset_id": "test"}


@pytest.mark.parametrize("subnational,row", [(False,NATIONAL),(True,REGIONAL)])
def test_accepts_one_valid_observation(subnational,row):
    validate_write_batch([dict(row)], subnational=subnational)


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), float("-inf"), True, "73"])
def test_rejects_bad_numeric_values(bad):
    validate = dict(REGIONAL, value=bad)
    with pytest.raises(ValueError, match="Invalid observation value"):
        validate_write_batch([dict(REGIONAL), validate], subnational=True)


def test_rejects_duplicate_keys_before_upsert():
    with pytest.raises(ValueError, match="Duplicate observation write key"):
        validate_write_batch([dict(NATIONAL), dict(NATIONAL, value=88)], subnational=False)


def test_duplicate_region_identity_uses_same_normalized_case():
    with pytest.raises(ValueError, match="Duplicate observation write key"):
        validate_write_batch([dict(REGIONAL), dict(REGIONAL, geo_code="es11")], subnational=True)


def test_bad_later_row_rejects_entire_batch():
    with pytest.raises(ValueError, match="Invalid observation period"):
        validate_write_batch([dict(REGIONAL), dict(REGIONAL, period="2025")], subnational=True)


@pytest.mark.parametrize(
    "subnational,row",
    [
        (False, dict(NATIONAL, country_iso3=" ESP")),
        (False, dict(NATIONAL, country_iso3="ESP ")),
        (True, dict(REGIONAL, geo_code=" ES11")),
        (True, dict(REGIONAL, geo_code="ES11 ")),
    ],
)
def test_rejects_geography_whitespace_before_database_access(subnational, row):
    with pytest.raises(ValueError, match="geography whitespace|Invalid national geography"):
        validate_write_batch([row], subnational=subnational)
