import pytest
from app.ingestion.oecd_tax_wedge import normalize_tax_wedge

HEAD = "REF_AREA,MEASURE,HH_TYPE,EARN_PRINCIPAL,EARN_SPOUSE,FREQ,TIME_PERIOD,OBS_VALUE,OBS_STATUS\n"


def test_retains_exact_household_scenario_and_real_period():
    rows = normalize_tax_wedge(HEAD + "ESP,AV_TW,S_C0,AW100,_Z,A,2025,41.44,A\n")
    assert len(rows) == 1
    assert rows[0]["period"] == 2025
    assert rows[0]["value"] == 41.44
    assert rows[0]["unit"] == "percent_of_total_labour_cost"
    assert rows[0]["observation_type"] == "observed"


def test_rejects_different_household_case():
    with pytest.raises(ValueError, match="dimensions"):
        normalize_tax_wedge(HEAD + "IRL,AV_TW,C_2,AW100,_Z,A,2025,32.6,A\n")


def test_rejects_unexpected_column_contract():
    with pytest.raises(ValueError, match="missing columns"):
        normalize_tax_wedge("REF_AREA,OBS_VALUE\nESP,41.4\n")


def test_no_synthetic_missing_values():
    assert normalize_tax_wedge(HEAD + "ESP,AV_TW,S_C0,AW100,_Z,A,2025,,M\n") == []
