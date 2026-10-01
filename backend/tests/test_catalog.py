from app.catalog import COUNTRIES, INDICATORS, SOURCES, country_config, world_bank_indicators


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



def test_initial_multi_country_registry():
    iso3 = {country["iso3"] for country in COUNTRIES}
    assert {"ESP", "PRT", "IRL"}.issubset(iso3)


def test_country_config_resolves_registered_country():
    assert country_config("prt")["iso2"] == "PT"
    assert country_config("IRL")["name"] == "Ireland"


def test_world_bank_catalog_excludes_source_specific_mappings():
    indicators = world_bank_indicators()
    assert indicators
    assert all(":" not in item["source_indicator"] for item in indicators)
    assert "population_total" in {item["indicator_id"] for item in indicators}
    assert "gdp_per_hour_worked" not in {item["indicator_id"] for item in indicators}
