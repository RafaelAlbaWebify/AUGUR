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
            allowed_country_iso3={"AUS", "JPN"},
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


LABOUR_CSV = """STRUCTURE,REF_AREA,Reference area,FREQ,MEASURE,Measure,UNIT_MEASURE,Unit of measure,AGE,Age,TERRITORIAL_LEVEL,Territorial level,TIME_PERIOD,OBS_VALUE
dataflow,AUS01F,Greater Sydney,A,EMP_RATIO,Employment to population ratio,PT_POP_SUB,Percentage of population in the same subgroup,Y15T64,15-64,FUA,FUA,2023,75.8
dataflow,AUS01F,Greater Sydney,A,LF_RATE,Labour force participation rate,PT_POP_SUB,Percentage of population in the same subgroup,Y15T64,15-64,FUA,FUA,2023,78.8
dataflow,AUS01F,Greater Sydney,A,UNE_RATE,Unemployment rate,PT_LF_SUB,Percentage of labour force in the same subgroup,Y15T64,15-64,FUA,FUA,2023,3.8
dataflow,AUS02F,Greater Melbourne,A,EMP_RATIO,Employment to population ratio,PT_POP_SUB,Percentage of population in the same subgroup,Y15T64,15-64,FUA,FUA,2023,74.9
dataflow,AUS01C,Greater Sydney,A,UNE_RATE,Unemployment rate,PT_LF_SUB,Percentage of labour force in the same subgroup,Y15T64,15-64,CITY,City,2023,3.5
dataflow,AT001F,Vienna,A,UNE_RATE,Unemployment rate,PT_LF_SUB,Percentage of labour force in the same subgroup,Y15T64,15-64,FUA,FUA,2023,6.0
"""


def test_normalize_fua_labour_keeps_comparable_rates_only():
    adapter = OECDFUAAdapter(client=None)
    try:
        rows = adapter.normalize_labour(
            LABOUR_CSV,
            countries=COUNTRIES,
            allowed_country_iso3={"AUS"},
        )
    finally:
        adapter.close()

    assert len(rows) == 4
    assert all(row["geo_level"] == "fua" for row in rows)
    assert all(row["unit"] == "percent" for row in rows)
    assert all(row["geo_code"] != "AUS01C" for row in rows)

    sydney = {
        row["indicator_id"]: row
        for row in rows
        if row["geo_code"] == "AUS01F"
    }
    assert sydney["urban_employment_to_population_ratio"]["value"] == 75.8
    assert sydney["urban_labour_force_participation_rate"]["value"] == 78.8
    assert sydney["urban_unemployment_rate"]["value"] == 3.8


def test_sync_fua_labour_persists_rate_history(monkeypatch):
    stored = []
    monkeypatch.setattr(
        module,
        "upsert_subnational_observations",
        lambda rows: stored.extend(rows) or len(rows),
    )

    adapter = OECDFUAAdapter(client=None)
    monkeypatch.setattr(
        adapter,
        "fetch_labour",
        lambda **kwargs: LABOUR_CSV,
    )

    try:
        result = adapter.sync_labour(
            countries=COUNTRIES,
            allowed_country_iso3={"AUS", "CAN"},
            start_year=2021,
        )
    finally:
        adapter.close()

    assert result["rows"] == 4
    assert result["country_count"] == 1
    assert result["covered_countries"] == ["AUS"]
    assert result["missing_countries"] == ["CAN"]
    assert result["complete"] is False
    assert result["fua_count"] == 2
    assert result["indicator_ids"] == [
        "urban_employment_to_population_ratio",
        "urban_labour_force_participation_rate",
        "urban_unemployment_rate",
    ]


TRANSPORT_CSV = """STRUCTURE,REF_AREA,Reference area,FREQ,MEASURE,Measure,UNIT_MEASURE,Unit of measure,TRAN_MODE,Mode of transport,TERRITORIAL_LEVEL,Territorial level,TRAVEL_TIME,Travel time,SERVICE,Service,TIME_PERIOD,OBS_VALUE
dataflow,AUS01F,Greater Sydney,A,POP_WITH_ACCESS,Population with access to at least one service point,PT_POP,Percentage of population,,Walking,FUA,FUA,MN_LE5,Within 5 minutes,PT_STOP,Public transport stop,2023,82.9
dataflow,AUS01F,Greater Sydney,A,POP_WITH_ACCESS,Population with access to at least one service point,PT_POP,Percentage of population,,Walking,FUA,FUA,MN_LE10,Within 10 minutes,PT_STOP,Public transport stop,2023,96.5
dataflow,AUS01F,Greater Sydney,A,POP_WITH_ACCESS,Population with access to at least one service point,PT_POP,Percentage of population,,Walking,FUA,FUA,MN_LE15,Within 15 minutes,PT_STOP,Public transport stop,2023,98.5
dataflow,AUS02F,Greater Melbourne,A,POP_WITH_ACCESS,Population with access to at least one service point,PT_POP,Percentage of population,,Walking,FUA,FUA,MN_LE10,Within 10 minutes,PT_STOP,Public transport stop,2023,95.0
dataflow,AUS01C,Greater Sydney,A,POP_WITH_ACCESS,Population with access to at least one service point,PT_POP,Percentage of population,,Walking,CITY,City,MN_LE10,Within 10 minutes,PT_STOP,Public transport stop,2023,99.0
dataflow,AT001F,Vienna,A,POP_WITH_ACCESS,Population with access to at least one service point,PT_POP,Percentage of population,,Walking,FUA,FUA,MN_LE10,Within 10 minutes,PT_STOP,Public transport stop,2023,97.0
"""


def test_normalize_fua_transport_keeps_three_access_thresholds():
    adapter = OECDFUAAdapter(client=None)
    try:
        rows = adapter.normalize_transport(
            TRANSPORT_CSV,
            countries=COUNTRIES,
            allowed_country_iso3={"AUS"},
        )
    finally:
        adapter.close()

    sydney = {
        row["indicator_id"]: row
        for row in rows
        if row["geo_code"] == "AUS01F"
    }
    assert sydney["urban_public_transport_access_5min"]["value"] == 82.9
    assert sydney["urban_public_transport_access_10min"]["value"] == 96.5
    assert sydney["urban_public_transport_access_15min"]["value"] == 98.5
    assert all(row["geo_level"] == "fua" for row in rows)
    assert all(row["unit"] == "percent" for row in rows)
    assert all(row["geo_code"] != "AUS01C" for row in rows)


def test_sync_fua_transport_persists_access_history(monkeypatch):
    stored = []
    monkeypatch.setattr(
        module,
        "upsert_subnational_observations",
        lambda rows: stored.extend(rows) or len(rows),
    )

    adapter = OECDFUAAdapter(client=None)
    monkeypatch.setattr(
        adapter,
        "fetch_transport",
        lambda **kwargs: TRANSPORT_CSV,
    )

    try:
        result = adapter.sync_transport(
            countries=COUNTRIES,
            allowed_country_iso3={"AUS", "CAN"},
            start_year=2019,
        )
    finally:
        adapter.close()

    assert result["rows"] == 4
    assert result["covered_countries"] == ["AUS"]
    assert result["missing_countries"] == ["CAN"]
    assert result["complete"] is False
    assert result["fua_count"] == 2
    assert result["indicator_ids"] == [
        "urban_public_transport_access_10min",
        "urban_public_transport_access_15min",
        "urban_public_transport_access_5min",
    ]


COMMUTE_CSV = """STRUCTURE,REF_AREA,Reference area,FREQ,MEASURE,Measure,UNIT_MEASURE,Unit of measure,TRAN_MODE,Mode of transport,TERRITORIAL_LEVEL,Territorial level,TRAVEL_TIME,Travel time,SERVICE,Service,TIME_PERIOD,OBS_VALUE,OBS_STATUS
dataflow,AUS01C,Greater Sydney,A,COMMUTE,Commute mode,PT_WR,Percentage of workers,CAR,Car,CITY,City,_Z,Not applicable,_Z,Not applicable,2021,52.0,A
dataflow,AUS01C,Greater Sydney,A,COMMUTE,Commute mode,PT_WR,Percentage of workers,PUBLIC_TRANSPORT,Public transport,CITY,City,_Z,Not applicable,_Z,Not applicable,2021,25.0,A
dataflow,AUS01C,Greater Sydney,A,COMMUTE,Commute mode,PT_WR,Percentage of workers,BIKE,Bicycle,CITY,City,_Z,Not applicable,_Z,Not applicable,2021,1.0,A
dataflow,AUS01C,Greater Sydney,A,COMMUTE,Commute mode,PT_WR,Percentage of workers,WALK,Walking,CITY,City,_Z,Not applicable,_Z,Not applicable,2021,4.0,A
dataflow,AUS01F,Greater Sydney,A,COMMUTE,Commute mode,PT_WR,Percentage of workers,CAR,Car,FUA,FUA,_Z,Not applicable,_Z,Not applicable,2021,61.0,A
dataflow,AUS01F,Greater Sydney,A,COMMUTE,Commute mode,PT_WR,Percentage of workers,PUBLIC_TRANSPORT,Public transport,FUA,FUA,_Z,Not applicable,_Z,Not applicable,2021,20.0,A
dataflow,AUS01F,Greater Sydney,A,COMMUTE,Commute mode,PS,Persons,PUBLIC_TRANSPORT,Public transport,FUA,FUA,_Z,Not applicable,_Z,Not applicable,2021,1000000,A
dataflow,AUS01F,Greater Sydney,A,COMMUTE,Commute mode,PT_WR,Percentage of workers,_O,Other,FUA,FUA,_Z,Not applicable,_Z,Not applicable,2021,3.0,A
dataflow,AT001F,Vienna,A,COMMUTE,Commute mode,PT_WR,Percentage of workers,WALK,Walking,FUA,FUA,_Z,Not applicable,_Z,Not applicable,2021,8.0,A
"""


def test_normalize_fua_commute_keeps_worker_shares_for_core_modes():
    adapter = OECDFUAAdapter(client=None)
    try:
        rows = adapter.normalize_commute(
            COMMUTE_CSV,
            countries=COUNTRIES,
            allowed_country_iso3={"AUS"},
        )
    finally:
        adapter.close()

    city = {
        row["indicator_id"]: row
        for row in rows
        if row["geo_code"] == "AUS01C"
    }
    assert city["urban_commute_car_share"]["value"] == 52.0
    assert city["urban_commute_public_transport_share"]["value"] == 25.0
    assert city["urban_commute_bicycle_share"]["value"] == 1.0
    assert city["urban_commute_walk_share"]["value"] == 4.0

    fua = {
        row["indicator_id"]: row
        for row in rows
        if row["geo_code"] == "AUS01F"
    }
    assert fua["urban_commute_car_share"]["value"] == 61.0
    assert fua["urban_commute_public_transport_share"]["value"] == 20.0

    assert all(row["unit"] == "percent" for row in rows)
    assert all(row["indicator_id"] != "_O" for row in rows)


def test_sync_fua_commute_persists_city_and_fua_worker_shares(monkeypatch):
    stored = []
    monkeypatch.setattr(
        module,
        "upsert_subnational_observations",
        lambda rows: stored.extend(rows) or len(rows),
    )

    adapter = OECDFUAAdapter(client=None)
    monkeypatch.setattr(
        adapter,
        "fetch_commute",
        lambda **kwargs: COMMUTE_CSV,
    )

    try:
        result = adapter.sync_commute(
            countries=COUNTRIES,
            allowed_country_iso3={"AUS", "CAN"},
            start_year=2019,
        )
    finally:
        adapter.close()

    assert result["rows"] == 6
    assert result["covered_countries"] == ["AUS"]
    assert result["missing_countries"] == ["CAN"]
    assert result["city_count"] == 1
    assert result["fua_count"] == 1
    assert set(result["indicator_ids"]) == {
        "urban_commute_car_share",
        "urban_commute_public_transport_share",
        "urban_commute_bicycle_share",
        "urban_commute_walk_share",
    }


GREEN_AREA_CSV = """STRUCTURE,REF_AREA,Reference area,FREQ,MEASURE,Measure,UNIT_MEASURE,Unit of measure,POLLUTANT_CONCENTRATION,Pollutant concentration level,TIME_SEASON,Time of the day and season,TERRITORIAL_LEVEL,Territorial level,TIME_PERIOD,OBS_VALUE
dataflow,AUS01F,Greater Sydney,A,GREEN_AREA,Green area in FUAs' urban centres,M2_PS,Square metres per person,_Z,Not applicable,_Z,Not applicable,FUA,FUA,2021,146
dataflow,AUS01F,Greater Sydney,A,GREEN_AREA,Green area in FUAs' urban centres,PT_LAR,Percentage of land area,_Z,Not applicable,_Z,Not applicable,FUA,FUA,2021,47.3
dataflow,AUS01C,Greater Sydney,A,GREEN_AREA,Green area in FUAs' urban centres,M2_PS,Square metres per person,_Z,Not applicable,_Z,Not applicable,CITY,City,2021,120
dataflow,AT001F,Vienna,A,GREEN_AREA,Green area in FUAs' urban centres,M2_PS,Square metres per person,_Z,Not applicable,_Z,Not applicable,FUA,FUA,2021,95
"""


def test_normalize_fua_green_area_keeps_two_fua_metrics_only():
    adapter = OECDFUAAdapter(client=None)
    try:
        rows = adapter.normalize_green_area(
            GREEN_AREA_CSV,
            countries=COUNTRIES,
            allowed_country_iso3={"AUS"},
        )
    finally:
        adapter.close()

    assert len(rows) == 2
    by_id = {row["indicator_id"]: row for row in rows}
    assert by_id["urban_green_area_per_capita_m2"]["value"] == 146.0
    assert by_id["urban_green_area_per_capita_m2"]["unit"] == "m2_per_person"
    assert by_id["urban_green_area_share"]["value"] == 47.3
    assert by_id["urban_green_area_share"]["unit"] == "percent"
    assert all(row["geo_level"] == "fua" for row in rows)
    assert all(row["geo_code"] == "AUS01F" for row in rows)


def test_sync_fua_green_area_reports_partial_country_coverage(monkeypatch):
    stored = []
    monkeypatch.setattr(
        module,
        "upsert_subnational_observations",
        lambda rows: stored.extend(rows) or len(rows),
    )

    adapter = OECDFUAAdapter(client=None)
    monkeypatch.setattr(
        adapter,
        "fetch_green_area",
        lambda **kwargs: GREEN_AREA_CSV,
    )

    try:
        result = adapter.sync_green_area(
            countries=COUNTRIES,
            allowed_country_iso3={"AUS", "CAN"},
            start_year=2020,
        )
    finally:
        adapter.close()

    assert result["rows"] == 2
    assert result["covered_countries"] == ["AUS"]
    assert result["missing_countries"] == ["CAN"]
    assert result["complete"] is False
    assert result["fua_count"] == 1
    assert set(result["indicator_ids"]) == {
        "urban_green_area_per_capita_m2",
        "urban_green_area_share",
    }


POLLUTION_CSV = """STRUCTURE,REF_AREA,Reference area,FREQ,MEASURE,Measure,UNIT_MEASURE,Unit of measure,POLLUTANT_CONCENTRATION,Pollutant concentration level,TIME_SEASON,Time of the day and season,TERRITORIAL_LEVEL,Territorial level,DESIGNATION,IUCN management categories,TIME_PERIOD,OBS_VALUE,OBS_STATUS,UNIT_MULT
dataflow,AUS01C,Greater Sydney,A,PM25_POP_EXP,Population exposure to PM2.5,MCG_M3,Microgrammes per cubic metre,_Z,Not applicable,_Z,Not applicable,CITY,City,_Z,Not applicable,2025,57.89089060915751,A,0
dataflow,AUS01F,Greater Sydney,A,PM25_POP_EXP,Population exposure to PM2.5,MCG_M3,Microgrammes per cubic metre,_Z,Not applicable,_Z,Not applicable,FUA,FUA,_Z,Not applicable,2025,52.4,A,0
dataflow,AT001C,Vienna,A,PM25_POP_EXP,Population exposure to PM2.5,MCG_M3,Microgrammes per cubic metre,_Z,Not applicable,_Z,Not applicable,CITY,City,_Z,Not applicable,2025,41.0,A,0
dataflow,AUS01C,Greater Sydney,A,OTHER,Other measure,MCG_M3,Microgrammes per cubic metre,_Z,Not applicable,_Z,Not applicable,CITY,City,_Z,Not applicable,2025,99.0,A,0
"""


def test_normalize_fua_pollution_keeps_pm25_population_exposure():
    adapter = OECDFUAAdapter(client=None)
    try:
        rows = adapter.normalize_pollution(
            POLLUTION_CSV,
            countries=COUNTRIES,
            allowed_country_iso3={"AUS"},
        )
    finally:
        adapter.close()

    assert len(rows) == 2
    assert {row["geo_code"] for row in rows} == {"AUS01C", "AUS01F"}
    assert {row["indicator_id"] for row in rows} == {
        "urban_pm25_population_exposure"
    }
    assert {row["unit"] for row in rows} == {"ug_m3"}
    assert all(row["dataset_id"] == "DSD_FUA_ENV@DF_POLLUTION" for row in rows)


def test_sync_fua_pollution_reports_coverage(monkeypatch):
    stored = []
    monkeypatch.setattr(
        module,
        "upsert_subnational_observations",
        lambda rows: stored.extend(rows) or len(rows),
    )

    adapter = OECDFUAAdapter(client=None)
    monkeypatch.setattr(
        adapter,
        "fetch_pollution",
        lambda **kwargs: POLLUTION_CSV,
    )

    try:
        result = adapter.sync_pollution(
            countries=COUNTRIES,
            allowed_country_iso3={"AUS", "CAN"},
            start_year=2020,
        )
    finally:
        adapter.close()

    assert result["rows"] == 2
    assert result["covered_countries"] == ["AUS"]
    assert result["missing_countries"] == ["CAN"]
    assert result["complete"] is False
    assert result["city_count"] == 1
    assert result["fua_count"] == 1
