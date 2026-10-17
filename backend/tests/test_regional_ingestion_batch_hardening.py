"""Regression coverage for shared regional labour/housing ingestion invariants."""
import copy
import math
import pytest
from app.ingestion.eurostat import EurostatAdapter
from app.ingestion.eurostat_regional_labour import normalize_subnational
from app.ingestion.eurostat_regional_contract import validate_eurostat_regional_rows
from app.ingestion.eurostat_regional_housing import (
    REGIONAL_HOUSING_SERIES, validate_housing_indicator_contracts,
)


def fixture():
    return {
        "id": ["geo", "time", "freq", "age", "sex", "unit"],
        "size": [1, 1, 1, 2, 1, 1],
        "dimension": {
            "geo": {"category": {"index": {"ES11": 0}}},
            "time": {"category": {"index": {"2025": 0}}},
            "freq": {"category": {"index": {"A": 0}}},
            "age": {"category": {"index": {"Y15-64": 0, "Y20-64": 1}}},
            "sex": {"category": {"index": {"T": 0}}},
            "unit": {"category": {"index": {"PC": 0}}},
        },
        "value": [67.4, 72.5],
        "status": {"1": "d"},
    }


CONFIG = {"indicator_id": "regional_employment_rate", "dataset_id": "lfst_r_lfe2emprt",
          "unit": "percent", "filters": {"freq": "A", "age": "Y20-64", "sex": "T", "unit": "PC", "geoLevel": "nuts2"}}


def test_only_exact_age_cohort_is_selected_with_provenance():
    rows = normalize_subnational(EurostatAdapter(), CONFIG, fixture())
    assert len(rows) == 1
    assert rows[0]["value"] == 72.5
    assert '"Y20-64"' in rows[0]["response_dimensions_json"]
    assert rows[0]["source_observation_status"] == "d"


def test_wrong_only_cohort_rejected():
    data = fixture()
    data["size"][3] = 1
    data["dimension"]["age"]["category"]["index"] = {"Y15-64": 0}
    data["value"] = [67.4]
    data["status"] = {}
    with pytest.raises(ValueError, match="No matching exact-dimension"):
        normalize_subnational(EurostatAdapter(), CONFIG, data)


@pytest.mark.parametrize("value", [float("nan"), float("inf"), True, "65"])
def test_invalid_regional_value_fails(value):
    data = fixture()
    data["value"][1] = value
    with pytest.raises(ValueError, match="Invalid regional observation"):
        normalize_subnational(EurostatAdapter(), CONFIG, data)


def test_housing_contract_matches_canonical_catalogue():
    validate_housing_indicator_contracts()


def test_housing_drift_rejected(monkeypatch):
    from app.ingestion import eurostat_regional_housing as housing
    altered = [{**row, "filters": {**row["filters"]}} for row in REGIONAL_HOUSING_SERIES]
    altered[0]["filters"]["unit"] = "EUR_HAB"
    monkeypatch.setattr(housing, "REGIONAL_HOUSING_SERIES", altered)
    with pytest.raises(ValueError, match="Regional housing dimension mismatch"):
        housing.validate_housing_indicator_contracts()


def test_duplicate_observation_prevents_upsert():
    row = {"geo_code": "ES11", "geo_level": "NUTS2", "indicator_id": "regional_employment_rate",
           "period": 2025, "value": 72.5, "unit": "percent", "source_id": "EUROSTAT",
           "dataset_id": "lfst_r_lfe2emprt"}
    with pytest.raises(ValueError, match="Duplicate regional observation"):
        validate_eurostat_regional_rows([row, dict(row)], allowed_indicators={"regional_employment_rate"})
