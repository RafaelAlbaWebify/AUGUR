from app.ingestion.eurostat_geography_discovery import discover_dataset_geographies, observed_geo_codes


def test_sparse_jsonstat_values_are_mapped_to_correct_regions():
    payload = {
        "id": ["geo", "time"], "size": [3, 2],
        "dimension": {"geo": {"category": {"index": {"ES11": 0, "BG31": 1, "FR10": 2}}}},
        "value": {"0": 14.0, "1": None, "2": None, "3": 0.0, "4": None, "5": None},
    }
    assert observed_geo_codes(payload) == {"ES11", "BG31"}
    result = discover_dataset_geographies(payload, "regional")
    assert result["region_count"] == 3
    assert result["observed_region_count"] == 2
    assert result["countries"]["BG"][0]["observation_status"] == "observed"
    assert result["countries"]["FR"][0]["observation_status"] == "no_numeric_observation"


def test_dimension_order_does_not_change_observed_geography():
    payload = {
        "id": ["time", "geo"], "size": [2, 2],
        "dimension": {"geo": {"category": {"index": {"BG31": 0, "FR10": 1}}}},
        "value": [None, 2.5, None, None],
    }
    assert observed_geo_codes(payload) == {"FR10"}


def test_boolean_and_nonfinite_values_are_not_observations():
    payload = {
        "id": ["geo"], "size": [3],
        "dimension": {"geo": {"category": {"index": {"ES11": 0, "BG31": 1, "FR10": 2}}}},
        "value": [True, float("nan"), -2.0],
    }
    assert observed_geo_codes(payload) == {"FR10"}
