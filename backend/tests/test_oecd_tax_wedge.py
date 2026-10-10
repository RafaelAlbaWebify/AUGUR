import pytest
from app.ingestion.oecd_tax_wedge import normalize_tax_wedge, fetch_tax_wedge_csv

HEAD = "REF_AREA,MEASURE,HOUSEHOLD_TYPE,INCOME_PRINCIPAL,INCOME_SPOUSE,FREQ,TIME_PERIOD,OBS_VALUE,OBS_STATUS\n"


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


def test_country_scoped_fetch_assembles_only_real_responses():
    import httpx
    urls = []
    def handler(request):
        urls.append(str(request.url))
        country = request.url.path.rsplit("/", 1)[-1].split(".")[0]
        return httpx.Response(200, text=HEAD + f"{country},AV_TW,S_C0,AW100,_Z,A,2025,40.0,A\n")
    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        rows = normalize_tax_wedge(fetch_tax_wedge_csv(client, start_year=2024))
    assert {r["country_iso3"] for r in rows} == {"ESP", "IRL", "PRT"}
    assert len(urls) == 3
    assert all("startPeriod=2024" in url for url in urls)
