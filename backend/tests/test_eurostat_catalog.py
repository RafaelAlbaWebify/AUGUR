from app.catalog import INDICATORS
from app.ingestion.eurostat import EUROSTAT_SERIES


def test_new_eu_dimensions_have_exact_eurostat_series():
    by_indicator = {item["indicator_id"]: item for item in EUROSTAT_SERIES}

    housing = by_indicator["housing_cost_overburden_rate"]
    assert housing["dataset_id"] == "ilc_lvho07a"
    assert housing["filters"]["incgrp"] == "TOTAL"
    assert housing["filters"]["age"] == "TOTAL"
    assert housing["filters"]["sex"] == "T"
    assert "unit" not in housing["filters"]

    education = by_indicator["tertiary_education_25_34"]
    assert education["dataset_id"] == "sdg_04_20"
    assert education["filters"]["age"] == "Y25-34"
    assert education["filters"]["isced11"] == "ED5-8"

    energy = by_indicator["energy_import_dependency"]
    assert energy["dataset_id"] == "nrg_ind_id"
    assert energy["filters"]["siec"] == "TOTAL"


def test_new_dimensions_are_registered_with_safe_interpretation():
    by_indicator = {item["indicator_id"]: item for item in INDICATORS}

    assert by_indicator["housing_cost_overburden_rate"]["dimension"] == "housing"
    assert by_indicator["housing_cost_overburden_rate"]["interpretation_policy"] == "lower"

    assert by_indicator["tertiary_education_25_34"]["dimension"] == "human_systems"
    assert by_indicator["tertiary_education_25_34"]["interpretation_policy"] == "higher"

    assert by_indicator["energy_import_dependency"]["dimension"] == "strategic_resilience"
    assert by_indicator["energy_import_dependency"]["interpretation_policy"] == "contextual"
