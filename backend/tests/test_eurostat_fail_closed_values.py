"""Fail-closed checks for malformed official Eurostat JSON-stat data."""
import copy
import pytest
from app.ingestion.eurostat import EurostatAdapter


def payload(value=5.0):
    return {
        "id": ["geo", "time"],
        "size": [1, 1],
        "dimension": {
            "geo": {"category": {"index": {"ES11": 0}}},
            "time": {"category": {"index": {"2025": 0}}},
        },
        "value": {"0": value},
    }


CONFIG = {"indicator_id": "test_rate", "dataset_id": "test_dataset", "unit": "percent",
          "dimension_values": {"geo": "ES11"}}


def test_valid_observation_is_retained():
    rows = EurostatAdapter().normalize("ESP", CONFIG, payload(0.0))
    assert len(rows) == 1
    assert rows[0]["value"] == 0.0


@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf"), True, "5"])
def test_invalid_observations_fail_closed(value):
    with pytest.raises(ValueError, match="Invalid Eurostat observation value"):
        EurostatAdapter().normalize("ESP", CONFIG, payload(value))


def test_bad_dimension_size_rejected():
    data = payload()
    data["size"] = [2, 1]
    with pytest.raises(ValueError, match="indexes do not match"):
        EurostatAdapter().normalize("ESP", CONFIG, data)


def test_duplicate_dimension_rejected():
    data = payload()
    data["id"] = ["geo", "geo"]
    with pytest.raises(ValueError, match="Invalid Eurostat dimension layout"):
        EurostatAdapter().normalize("ESP", CONFIG, data)
