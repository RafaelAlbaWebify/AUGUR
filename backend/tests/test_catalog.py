from app.catalog import INDICATORS, SOURCES


VALID_POLICIES = {
    "higher",
    "lower",
    "target_range",
    "contextual",
}


def test_indicator_ids_are_unique():
    ids = [indicator["indicator_id"] for indicator in INDICATORS]
    assert len(ids) == len(set(ids))


def test_source_ids_are_unique():
    ids = [source["source_id"] for source in SOURCES]
    assert len(ids) == len(set(ids))


def test_indicator_policies_are_valid():
    for indicator in INDICATORS:
        assert indicator["interpretation_policy"] in VALID_POLICIES


def test_target_range_indicators_have_complete_bounds():
    for indicator in INDICATORS:
        if indicator["interpretation_policy"] != "target_range":
            continue

        assert indicator["target_min"] is not None
        assert indicator["target_max"] is not None
        assert indicator["target_min"] < indicator["target_max"]


def test_eurostat_has_higher_priority_than_world_bank_for_eu_data():
    priority = {source["source_id"]: source["priority"] for source in SOURCES}

    assert priority["EUROSTAT"] < priority["WORLD_BANK"]
