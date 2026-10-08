from app.ingestion import oecd_fua as module
from app.ingestion.oecd_fua import OECDFUAAdapter


FUA_CSV = """STRUCTURE,STRUCTURE_ID,STRUCTURE_NAME,ACTION,REF_AREA,Reference area,FREQ,Frequency of observation,MEASURE,Measure,UNIT_MEASURE,Unit of measure,TERRITORIAL_LEVEL,Territorial level,TIME_PERIOD,Time period,OBS_VALUE,Observation value,OBS_STATUS,Observation status,UNIT_MULT,Unit multiplier,DECIMALS,Decimals
dataflow,OECD.CFE.EDS:DSD_FUA_TERR@DF_DENSITY(1.1),Population density,I,AUS01C,Greater Sydney,A,Annual,POP_DEN,Population density,PS_KM2,Persons per square kilometre,CITY,City,2020,2020,2376,2376,A,Normal value,0,Units,0,Zero
dataflow,OECD.CFE.EDS:DSD_FUA_TERR@DF_DENSITY(1.1),Population density,I,AUS01F,Sydney FUA,A,Annual,POP_DEN,Population density,PS_KM2,Persons per square kilometre,FUA,Functional urban area,2020,2020,421,421,A,Normal value,0,Units,0,Zero
dataflow,OECD.CFE.EDS:DSD_FUA_TERR@DF_DENSITY(1.1),Population density,I,AT001C,Vienna,A,Annual,POP_DEN,Population density,PS_KM2,Persons per square kilometre,CITY,City,2020,2020,4700,4700,A,Normal value,0,Units,0,Zero
dataflow,OECD.CFE.EDS:DSD_FUA_TERR@DF_DENSITY(1.1),Population density,I,CAN01C,Toronto,A,Annual,POP_DEN,Population density,PS_KM2,Persons per square kilometre,CITY,City,2020,2020,2800,2800,A,Normal value,0,Units,0,Zero
"""


COUNTRIES = [
    {"iso2": "AU", "iso3": "AUS", "name": "Australia"},
    {"iso2": "AT", "iso3": "AUT", "name": "Austria"},
    {"iso2": "CA", "iso3": "CAN", "name": "Canada"},
]


def test_normalize_fua_density_resolves_mixed_country_prefixes():
    adapter = OECDFUAAdapter(client=None)
    try:
        rows = adapter.normalize_density(
            FUA_CSV,
            countries=COUNTRIES,
        )
    finally:
        adapter.close()

    assert len(rows) == 4

    sydney = next(row for row in rows if row["geo_code"] == "AUS01C")
    assert sydney["country_iso3"] == "AUS"
    assert sydney["country_iso2"] == "AU"
    assert sydney["geo_level"] == "city"
    assert sydney["geography_system"] == "OECD_FUA"
    assert sydney["indicator_id"] == "urban_population_density"
    assert sydney["value"] == 2376.0

    sydney_fua = next(row for row in rows if row["geo_code"] == "AUS01F")
    assert sydney_fua["geo_level"] == "fua"
    assert sydney_fua["country_iso3"] == "AUS"

    vienna = next(row for row in rows if row["geo_code"] == "AT001C")
    assert vienna["country_iso3"] == "AUT"

    toronto = next(row for row in rows if row["geo_code"] == "CAN01C")
    assert toronto["country_iso3"] == "CAN"


def test_normalize_fua_density_can_filter_non_eu_oecd_targets():
    adapter = OECDFUAAdapter(client=None)
    try:
        rows = adapter.normalize_density(
            FUA_CSV,
            countries=COUNTRIES,
            allowed_country_iso3={"AUS", "CAN"},
        )
    finally:
        adapter.close()

    assert {row["country_iso3"] for row in rows} == {"AUS", "CAN"}
    assert all(row["country_iso3"] != "AUT" for row in rows)


def test_normalize_fua_density_falls_back_to_code_suffix_for_level():
    csv_text = FUA_CSV.replace(",CITY,City,", ",,,")

    adapter = OECDFUAAdapter(client=None)
    try:
        rows = adapter.normalize_density(
            csv_text,
            countries=COUNTRIES,
        )
    finally:
        adapter.close()

    sydney = next(row for row in rows if row["geo_code"] == "AUS01C")
    assert sydney["geo_level"] == "city"


def test_sync_fua_density_persists_history(monkeypatch):
    stored = []
    monkeypatch.setattr(
        module,
        "upsert_subnational_observations",
        lambda rows: stored.extend(rows) or len(rows),
    )

    adapter = OECDFUAAdapter(client=None)
    monkeypatch.setattr(
        adapter,
        "fetch_density",
        lambda **kwargs: FUA_CSV,
    )

    try:
        result = adapter.sync_density(
            countries=COUNTRIES,
            allowed_country_iso3={"AUS"},
            start_year=2020,
        )
    finally:
        adapter.close()

    assert result["rows"] == 2
    assert result["country_count"] == 1
    assert result["geography_count"] == 2
    assert result["city_count"] == 1
    assert result["fua_count"] == 1
    assert {row["geo_code"] for row in stored} == {"AUS01C", "AUS01F"}
