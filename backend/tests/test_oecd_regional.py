from app.ingestion import oecd_regional as module
from app.ingestion.oecd_regional import OECDRegionalAdapter


CSV_WITH_LABELS = """DATAFLOW,FREQ,Frequency of observation,TERRITORIAL_LEVEL,Territorial level,REF_AREA,Reference area,TERRITORIAL_TYPE,MEASURE,AGE,SEX,UNIT_MEASURE,Unit of measure,TIME_PERIOD,OBS_VALUE,COUNTRY,OBS_STATUS,UNIT_MULT,DECIMALS
OECD.CFE.EDS, A,Annual,TL2,Large region (TL2),AU1,New South Wales,,DENSITY,_T,_T,PS_KM2,Persons per square kilometre,2024,10.58,AUS,A,0,2
OECD.CFE.EDS,A,Annual,TL2,Large region (TL2),AU2,Victoria,,DENSITY,_T,_T,PS_KM2,Persons per square kilometre,2024,30.66,AUS,A,0,2
OECD.CFE.EDS,A,Annual,TL3,Small region (TL3),US011,Example US region,,DENSITY,_T,_T,PS_KM2,Persons per square kilometre,2024,44.2,USA,A,0,2
OECD.CFE.EDS,A,Annual,CTRY,Country,AUS,Australia,,DENSITY,_T,_T,PS_KM2,Persons per square kilometre,2024,3.4,AUS,A,0,2
OECD.CFE.EDS,A,Annual,TL2,Large region (TL2),AU1,New South Wales,,AREA,_T,_T,KM2,Square kilometres,2024,800000,AUS,A,0,2
"""


def test_normalize_density_preserves_oecd_geography_identity():
    adapter = OECDRegionalAdapter(client=None)
    try:
        rows = adapter.normalize_density(CSV_WITH_LABELS)
    finally:
        adapter.close()

    assert len(rows) == 3

    au1 = next(row for row in rows if row["geo_code"] == "AU1")
    assert au1["geo_name"] == "New South Wales"
    assert au1["geo_level"] == "tl2"
    assert au1["country_iso3"] == "AUS"
    assert au1["country_iso2"] == "AU"
    assert au1["geography_system"] == "OECD_TL_2024"
    assert au1["indicator_id"] == "regional_population_density"
    assert au1["value"] == 10.58
    assert au1["unit"] == "people_per_km2"


def test_normalize_density_can_filter_registered_countries():
    adapter = OECDRegionalAdapter(client=None)
    try:
        rows = adapter.normalize_density(
            CSV_WITH_LABELS,
            allowed_country_iso3={"USA"},
        )
    finally:
        adapter.close()

    assert len(rows) == 1
    assert rows[0]["geo_code"] == "US011"
    assert rows[0]["country_iso3"] == "USA"
    assert rows[0]["geo_level"] == "tl3"


def test_sync_density_writes_normalized_rows(monkeypatch):
    stored = []
    monkeypatch.setattr(
        module,
        "upsert_subnational_observations",
        lambda rows: stored.extend(rows) or len(rows),
    )

    adapter = OECDRegionalAdapter(client=None)
    monkeypatch.setattr(
        adapter,
        "fetch_density",
        lambda **kwargs: CSV_WITH_LABELS,
    )

    try:
        result = adapter.sync_density(
            allowed_country_iso3={"AUS"},
            start_year=2024,
            end_year=2024,
        )
    finally:
        adapter.close()

    assert result["rows"] == 2
    assert result["countries"] == ["AUS"]
    assert result["geography_count"] == 2
    assert result["geo_levels"] == ["tl2"]
    assert result["period_min"] == 2024
    assert result["period_max"] == 2024
    assert {row["geo_name"] for row in stored} == {
        "New South Wales",
        "Victoria",
    }
