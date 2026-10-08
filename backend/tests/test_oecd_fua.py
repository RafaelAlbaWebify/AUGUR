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
            allowed_country_iso3={"AUS", "JPN"},
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
            allowed_country_iso3={"AUS", "CAN"},
            start_year=2020,
        )
    finally:
        adapter.close()

    assert result["rows"] == 2
    assert result["country_count"] == 1
    assert result["covered_countries"] == ["AUS"]
    assert result["missing_countries"] == ["JPN"]
    assert result["complete"] is False
    assert result["geography_count"] == 2
    assert result["city_count"] == 1
    assert result["fua_count"] == 1
    assert {row["geo_code"] for row in stored} == {"AUS01C", "AUS01F"}


POPULATION_CSV = """STRUCTURE,STRUCTURE_ID,STRUCTURE_NAME,ACTION,REF_AREA,Reference area,FREQ,Frequency of observation,MEASURE,Measure,UNIT_MEASURE,Unit of measure,AGE,Age,SEX,Sex,TERRITORIAL_LEVEL,Territorial level,TIME_PERIOD,Time period,OBS_VALUE,Observation value,OBS_STATUS,Observation status
dataflow,OECD.CFE.EDS:DSD_FUA_DEMO@DF_AGE_SEX(1.2),Population by age and sex,I,AUS01C,Greater Sydney,A,Annual,POP,Population,PS,Persons,_T,Total,_T,Total,CITY,City,2024,2024,5570000,5570000,A,Normal value
dataflow,OECD.CFE.EDS:DSD_FUA_DEMO@DF_AGE_SEX(1.2),Population by age and sex,I,AUS01F,Sydney FUA,A,Annual,POP,Population,PS,Persons,_T,Total,_T,Total,FUA,Functional urban area,2024,2024,5850000,5850000,A,Normal value
dataflow,OECD.CFE.EDS:DSD_FUA_DEMO@DF_AGE_SEX(1.2),Population by age and sex,I,AUS01C,Greater Sydney,A,Annual,POP,Population,PS,Persons,Y0T4,0-4,_T,Total,CITY,City,2024,2024,300000,300000,A,Normal value
dataflow,OECD.CFE.EDS:DSD_FUA_DEMO@DF_AGE_SEX(1.2),Population by age and sex,I,AT001C,Vienna,A,Annual,POP,Population,PS,Persons,_T,Total,_T,Total,CITY,City,2024,2024,2000000,2000000,A,Normal value
"""


def test_normalize_fua_population_keeps_total_population_only():
    adapter = OECDFUAAdapter(client=None)
    try:
        rows = adapter.normalize_population(
            POPULATION_CSV,
            countries=COUNTRIES,
            allowed_country_iso3={"AUS"},
        )
    finally:
        adapter.close()

    assert len(rows) == 2
    assert {row["geo_code"] for row in rows} == {"AUS01C", "AUS01F"}
    assert {row["indicator_id"] for row in rows} == {"urban_population"}
    assert {row["unit"] for row in rows} == {"persons"}
    assert {row["value"] for row in rows} == {5570000.0, 5850000.0}


def test_sync_fua_population_persists_history(monkeypatch):
    stored = []
    monkeypatch.setattr(
        module,
        "upsert_subnational_observations",
        lambda rows: stored.extend(rows) or len(rows),
    )

    adapter = OECDFUAAdapter(client=None)
    monkeypatch.setattr(
        adapter,
        "fetch_population",
        lambda **kwargs: POPULATION_CSV,
    )

    try:
        result = adapter.sync_population(
            countries=COUNTRIES,
            allowed_country_iso3={"AUS", "CAN"},
            start_year=2021,
        )
    finally:
        adapter.close()

    assert result["rows"] == 2
    assert result["country_count"] == 1
    assert result["geography_count"] == 2
    assert result["city_count"] == 1
    assert result["fua_count"] == 1


DEPENDENCY_CSV = """STRUCTURE,REF_AREA,Reference area,FREQ,MEASURE,Measure,UNIT_MEASURE,Unit of measure,AGE,Age,SEX,ORIGIN,TERRITORIAL_LEVEL,Territorial level,CITIZENSHIP,TIME_PERIOD,OBS_VALUE
dataflow,AUS01C,Greater Sydney,A,DEPEND_RATIO,Dependency ratio,PT_POP_Y15T64,Percentage of population aged 15-64 years,Y_LT15_GE65,Less than 15 years or 65 years or over,_T,_T,CITY,City,_T,2022,48.4
dataflow,AUS01C,Greater Sydney,A,DEPEND_RATIO,Dependency ratio,PT_POP_Y15T64,Percentage of population aged 15-64 years,Y_LT15,Less than 15 years,_T,_T,CITY,City,_T,2024,24.8
dataflow,AUS01C,Greater Sydney,A,DEPEND_RATIO,Dependency ratio,PT_POP_Y15T64,Percentage of population aged 15-64 years,Y_GE65,65 years or over,_T,_T,CITY,City,_T,2024,21.6
dataflow,AUS01F,Greater Sydney,A,DEPEND_RATIO,Dependency ratio,PT_POP_Y15T64,Percentage of population aged 15-64 years,Y_LT15_GE65,Less than 15 years or 65 years or over,_T,_T,FUA,FUA,_T,2023,49.0
dataflow,AT001C,Vienna,A,DEPEND_RATIO,Dependency ratio,PT_POP_Y15T64,Percentage of population aged 15-64 years,Y_LT15_GE65,Less than 15 years or 65 years or over,_T,_T,CITY,City,_T,2024,48.0
"""


def test_normalize_fua_dependency_keeps_three_distinct_ratios():
    adapter = OECDFUAAdapter(client=None)
    try:
        rows = adapter.normalize_dependency(
            DEPENDENCY_CSV,
            countries=COUNTRIES,
            allowed_country_iso3={"AUS"},
        )
    finally:
        adapter.close()

    assert len(rows) == 4
    city_rows = {
        row["indicator_id"]: row
        for row in rows
        if row["geo_code"] == "AUS01C"
    }
    assert city_rows["urban_total_dependency_ratio"]["value"] == 48.4
    assert city_rows["urban_youth_dependency_ratio"]["value"] == 24.8
    assert city_rows["urban_old_age_dependency_ratio"]["value"] == 21.6
    assert all(row["unit"] == "percent" for row in city_rows.values())

    fua = next(
        row
        for row in rows
        if row["geo_code"] == "AUS01F"
    )
    assert fua["indicator_id"] == "urban_total_dependency_ratio"
    assert fua["geo_level"] == "fua"
    assert fua["value"] == 49.0


def test_sync_fua_dependency_persists_selected_ratios(monkeypatch):
    stored = []
    monkeypatch.setattr(
        module,
        "upsert_subnational_observations",
        lambda rows: stored.extend(rows) or len(rows),
    )

    adapter = OECDFUAAdapter(client=None)
    monkeypatch.setattr(
        adapter,
        "fetch_dependency",
        lambda **kwargs: DEPENDENCY_CSV,
    )

    try:
        result = adapter.sync_dependency(
            countries=COUNTRIES,
            allowed_country_iso3={"AUS"},
            start_year=2021,
        )
    finally:
        adapter.close()

    assert result["rows"] == 4
    assert result["country_count"] == 1
    assert result["covered_countries"] == ["AUS"]
    assert result["missing_countries"] == []
    assert result["complete"] is True
    assert result["geography_count"] == 2
    assert result["indicator_ids"] == [
        "urban_old_age_dependency_ratio",
        "urban_total_dependency_ratio",
        "urban_youth_dependency_ratio",
    ]
