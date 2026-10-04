from app.catalog import INDICATORS
from app.ingestion.eurostat import EUROSTAT_JOB_VACANCY_RATES, EUROSTAT_SERIES


def test_new_eu_dimensions_have_exact_eurostat_series():
    by_indicator = {item["indicator_id"]: item for item in EUROSTAT_SERIES}

    price_level = by_indicator["household_price_level_index"]
    assert price_level["dataset_id"] == "prc_ppp_ind"
    assert price_level["filters"]["na_item"] == "PLI_EU27_2020"
    assert price_level["filters"]["ppp_cat"] == "E011"

    house_prices = by_indicator["real_house_price_index"]
    assert house_prices["dataset_id"] == "tipsho10"
    assert house_prices["filters"]["unit"] == "I15_A_AVG"

    rents = by_indicator["rent_price_index"]
    assert rents["dataset_id"] == "prc_hicp_aind"
    assert rents["filters"]["unit"] == "INX_A_AVG"
    assert rents["filters"]["coicop"] == "CP041"

    housing = by_indicator["housing_cost_overburden_rate"]
    assert housing["dataset_id"] == "tessi163"
    assert housing["filters"]["unit"] == "PC"
    assert housing["filters"]["rskpovth"] == "TOTAL"
    assert housing["filters"]["age"] == "TOTAL"
    assert housing["filters"]["sex"] == "T"

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



def test_housing_market_pressure_indicators_are_directional():
    by_indicator = {item["indicator_id"]: item for item in INDICATORS}

    assert by_indicator["real_house_price_index"]["dimension"] == "housing"
    assert by_indicator["real_house_price_index"]["interpretation_policy"] == "lower"

    assert by_indicator["rent_price_index"]["dimension"] == "housing"
    assert by_indicator["rent_price_index"]["interpretation_policy"] == "lower"


def test_safety_and_environment_series_are_registered_from_official_eu_sources():
    by_indicator = {item["indicator_id"]: item for item in EUROSTAT_SERIES}

    safety = by_indicator["intentional_homicide_rate"]
    assert safety["dataset_id"] == "crim_off_cat"
    assert safety["filters"]["iccs"] == "ICCS0101"
    assert safety["filters"]["unit"] == "P_HTHAB"

    environment = by_indicator["pm25_premature_death_rate"]
    assert environment["dataset_id"] == "sdg_11_52"
    assert environment["label_contains"]["unit"] == "Rate"


def test_safety_and_environment_interpret_lower_values_as_better():
    by_indicator = {item["indicator_id"]: item for item in INDICATORS}

    assert by_indicator["intentional_homicide_rate"]["dimension"] == "safety"
    assert by_indicator["intentional_homicide_rate"]["interpretation_policy"] == "lower"

    assert by_indicator["pm25_premature_death_rate"]["dimension"] == "environment"
    assert by_indicator["pm25_premature_death_rate"]["interpretation_policy"] == "lower"


def test_infrastructure_baseline_uses_official_household_connectivity_series():
    by_series = {item["indicator_id"]: item for item in EUROSTAT_SERIES}
    by_indicator = {item["indicator_id"]: item for item in INDICATORS}

    series = by_series["household_internet_access"]
    assert series["dataset_id"] == "tin00134"
    assert series["filters"]["unit"] == "PC_HH"
    assert series["filters"]["hhtyp"] == "TOTAL"

    indicator = by_indicator["household_internet_access"]
    assert indicator["dimension"] == "infrastructure"
    assert indicator["interpretation_policy"] == "higher"


def test_aic_material_welfare_indicator_uses_current_ppp_dataset():
    by_series = {item["indicator_id"]: item for item in EUROSTAT_SERIES}
    by_indicator = {item["indicator_id"]: item for item in INDICATORS}

    series = by_series["actual_individual_consumption_index"]
    assert series["dataset_id"] == "prc_ppp_ind_1"
    assert series["filters"]["indic_ppp"] == "VI_PPS_EU27_2020_HAB"
    assert series["filters"]["ppp_cat18"] == "A01"

    indicator = by_indicator["actual_individual_consumption_index"]
    assert indicator["dimension"] == "prosperity"
    assert indicator["interpretation_policy"] == "higher"
    assert "household material welfare" in indicator["comparability_note"]


def test_experimental_vacancy_source_has_explicit_country_coverage():
    assert EUROSTAT_JOB_VACANCY_RATES["dataset_id"] == "jvs_a_isco3_r1"
    assert EUROSTAT_JOB_VACANCY_RATES["filters"]["freq"] == "A"
    assert EUROSTAT_JOB_VACANCY_RATES["supported_iso3"] == {"ESP", "PRT"}
    assert "IRL" not in EUROSTAT_JOB_VACANCY_RATES["supported_iso3"]


def test_unmet_medical_needs_uses_eu_silc_access_measure():
    by_series = {item["indicator_id"]: item for item in EUROSTAT_SERIES}
    by_indicator = {item["indicator_id"]: item for item in INDICATORS}

    series = by_series["unmet_medical_needs"]
    assert series["dataset_id"] == "hlth_silc_08b"
    assert series["filters"]["unit"] == "PC"
    assert series["filters"]["reason"] == "TXP_TFAR_WLIST"
    assert series["filters"]["rskpovth"] == "TOTAL"
    assert series["filters"]["sex"] == "T"
    assert series["filters"]["age"] == "Y_GE16"

    indicator = by_indicator["unmet_medical_needs"]
    assert indicator["dimension"] == "human_systems"
    assert indicator["interpretation_policy"] == "lower"
