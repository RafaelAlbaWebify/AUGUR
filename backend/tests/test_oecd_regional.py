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


POPULATION_CSV = """STRUCTURE,STRUCTURE_ID,STRUCTURE_NAME,ACTION,FREQ,Frequency of observation,TERRITORIAL_LEVEL,Territorial level,REF_AREA,Reference area,TERRITORIAL_TYPE,Territorial typology,MEASURE,Measure,AGE,Age,SEX,Sex,UNIT_MEASURE,Unit of measure,TIME_PERIOD,Time period,OBS_VALUE,Observation value,COUNTRY,Country,OBS_STATUS,Observation status,UNIT_MULT,Unit multiplier,DECIMALS,Decimals
dataflow,OECD.CFE.EDS:DSD_REG_DEMO@DF_POP_BROAD(2.4),Population by broad age groups - Regions,I,A,Annual,TL2,Large region (TL2),AU1,New South Wales,,,POP,Population,_T,Total,_T,Total,PS,Persons,2024,2024,8534000,8534000,AUS,Australia,A,Normal value,0,Units,0,Zero
dataflow,OECD.CFE.EDS:DSD_REG_DEMO@DF_POP_BROAD(2.4),Population by broad age groups - Regions,I,A,Annual,TL2,Large region (TL2),AU2,Victoria,,,POP,Population,_T,Total,_T,Total,PS,Persons,2024,2024,6959000,6959000,AUS,Australia,A,Normal value,0,Units,0,Zero
dataflow,OECD.CFE.EDS:DSD_REG_DEMO@DF_POP_BROAD(2.4),Population by broad age groups - Regions,I,A,Annual,TL2,Large region (TL2),AU1,New South Wales,,,POP,Population,Y0T14,0-14,_T,Total,PS,Persons,2024,2024,1600000,1600000,AUS,Australia,A,Normal value,0,Units,0,Zero
"""


def test_normalize_population_keeps_total_population_only():
    adapter = OECDRegionalAdapter(client=None)
    try:
        rows = adapter.normalize_population(
            POPULATION_CSV,
            allowed_country_iso3={"AUS"},
        )
    finally:
        adapter.close()

    assert len(rows) == 2
    assert {row["geo_code"] for row in rows} == {"AU1", "AU2"}
    assert {row["indicator_id"] for row in rows} == {"regional_population"}
    assert {row["unit"] for row in rows} == {"persons"}
    assert {row["geo_name"] for row in rows} == {
        "New South Wales",
        "Victoria",
    }


def test_sync_population_writes_oecd_tl2_rows(monkeypatch):
    stored = []
    monkeypatch.setattr(
        module,
        "upsert_subnational_observations",
        lambda rows: stored.extend(rows) or len(rows),
    )

    adapter = OECDRegionalAdapter(client=None)
    monkeypatch.setattr(
        adapter,
        "fetch_population",
        lambda **kwargs: POPULATION_CSV,
    )

    try:
        result = adapter.sync_population(
            allowed_country_iso3={"AUS"},
            start_year=2024,
            end_year=2024,
        )
    finally:
        adapter.close()

    assert result["rows"] == 2
    assert result["country_count"] == 1
    assert result["geography_count"] == 2
    assert result["geo_levels"] == ["tl2"]
    assert {row["value"] for row in stored} == {8534000.0, 6959000.0}


def test_fetch_defaults_use_all_tl2_tl3_keys():
    class Response:
        def __init__(self, text):
            self.text = text

        def raise_for_status(self):
            return None

    class Client:
        def __init__(self):
            self.calls = []

        def get(self, url, params):
            self.calls.append((url, params))
            if "DF_DENSITY" in url:
                return Response(CSV_WITH_LABELS)
            return Response(POPULATION_CSV)

    client = Client()
    adapter = OECDRegionalAdapter(client=client)

    density = adapter.fetch_density(start_year=2021)
    population = adapter.fetch_population(start_year=2021)

    assert density == CSV_WITH_LABELS
    assert population == POPULATION_CSV
    assert client.calls[0][0].endswith(
        "/A.TL2+TL3......PS_KM2"
    )
    assert client.calls[1][0].endswith(
        "/A.TL2+TL3...POP._T._T."
    )


DEMOGRAPHY_CSV = """STRUCTURE,FREQ,TERRITORIAL_LEVEL,REF_AREA,Reference area,TERRITORIAL_TYPE,MEASURE,Measure,AGE,SEX,UNIT_MEASURE,Unit of measure,TIME_PERIOD,OBS_VALUE,COUNTRY
dataflow,A,TL2,AU1,New South Wales,,INMIG,New residents in the region coming from another country,_T,_T,PT_POP,Percentage of population,2023,3.1,AUS
dataflow,A,TL2,AU1,New South Wales,,INMIG,New residents in the region coming from another country,_T,_T,PS,Persons,2023,250037,AUS
dataflow,A,TL2,AU1,New South Wales,,OUTMIG,Persons who left the region to reside in another country,_T,_T,PT_POP,Percentage of population,2023,1.2,AUS
dataflow,A,TL2,AU1,New South Wales,,NETMOB,Net internal mobility,_T,_T,PT_POP,Percentage of population,2023,-0.4,AUS
dataflow,A,TL2,AU1,New South Wales,,MORT_STANDARD_RATIO,Age-adjusted mortality rate,_T,_T,10P3HB,Per 1 000 inhabitants,2022,5.6,AUS
dataflow,A,TL2,AU1,New South Wales,,MORT,Deaths,_T,_T,DT,Deaths,2023,60000,AUS
dataflow,A,TL3,US011,Example US region,,INMIG,New residents in the region coming from another country,_T,_T,PT_POP,Percentage of population,2023,2.2,USA
"""


def test_normalize_demography_keeps_comparable_metric_units_only():
    adapter = OECDRegionalAdapter(client=None)
    try:
        rows = adapter.normalize_demography(
            DEMOGRAPHY_CSV,
            allowed_country_iso3={"AUS"},
        )
    finally:
        adapter.close()

    assert len(rows) == 4
    by_id = {row["indicator_id"]: row for row in rows}

    assert by_id["regional_international_inmigration_share"]["value"] == 3.1
    assert by_id["regional_international_inmigration_share"]["unit"] == "percent"
    assert by_id["regional_international_outmigration_share"]["value"] == 1.2
    assert by_id["regional_net_internal_mobility_share"]["value"] == -0.4
    assert by_id["regional_age_adjusted_mortality_per_1000"]["value"] == 5.6
    assert by_id["regional_age_adjusted_mortality_per_1000"]["unit"] == "per_1000_people"
    assert all(row["country_iso3"] == "AUS" for row in rows)


def test_sync_demography_writes_selected_oecd_metrics(monkeypatch):
    stored = []
    monkeypatch.setattr(
        module,
        "upsert_subnational_observations",
        lambda rows: stored.extend(rows) or len(rows),
    )

    adapter = OECDRegionalAdapter(client=None)
    monkeypatch.setattr(
        adapter,
        "fetch_demography",
        lambda **kwargs: DEMOGRAPHY_CSV,
    )

    try:
        result = adapter.sync_demography(
            allowed_country_iso3={"AUS"},
            start_year=2021,
        )
    finally:
        adapter.close()

    assert result["rows"] == 4
    assert result["country_count"] == 1
    assert result["geography_count"] == 1
    assert result["geo_levels"] == ["tl2"]
    assert result["indicator_ids"] == [
        "regional_age_adjusted_mortality_per_1000",
        "regional_international_inmigration_share",
        "regional_international_outmigration_share",
        "regional_net_internal_mobility_share",
    ]


LABOUR_CSV = """STRUCTURE,FREQ,TERRITORIAL_LEVEL,REF_AREA,Reference area,TERRITORIAL_TYPE,MEASURE,Measure,AGE,SEX,UNIT_MEASURE,Unit of measure,TIME_PERIOD,OBS_VALUE,COUNTRY
dataflow,A,TL2,AU1,New South Wales,,EMP_RATIO,Employment to population ratio,Y15T64,_T,PT_POP_SUB,Percentage of population in the same subgroup,2024,76.5,AUS
dataflow,A,TL2,AU2,Victoria,,EMP_RATIO,Employment to population ratio,Y15T64,_T,PT_POP_SUB,Percentage of population in the same subgroup,2024,77.2,AUS
dataflow,A,TL2,AU1,New South Wales,,UNE_RATE,Unemployment rate,Y15T64,_T,PT_LF_SUB,Percentage of labour force in the same subgroup,2024,4.0,AUS
dataflow,A,TL2,AU2,Victoria,,UNE_RATE,Unemployment rate,Y15T64,_T,PT_LF_SUB,Percentage of labour force in the same subgroup,2024,4.2,AUS
dataflow,A,TL3,US011,Example US region,,EMP_RATIO,Employment to population ratio,Y15T64,_T,PT_POP_SUB,Percentage of population in the same subgroup,2024,73.1,USA
dataflow,A,TL2,AU1,New South Wales,,EMP_RATIO,Employment to population ratio,Y15T64,F,PT_POP_SUB,Percentage of population in the same subgroup,2024,72.0,AUS
"""


def test_normalize_labour_keeps_total_15_64_employment_ratio():
    adapter = OECDRegionalAdapter(client=None)
    try:
        rows = adapter.normalize_labour(
            LABOUR_CSV,
            allowed_country_iso3={"AUS"},
        )
    finally:
        adapter.close()

    assert len(rows) == 4
    assert {row["geo_code"] for row in rows} == {"AU1", "AU2"}
    assert {row["indicator_id"] for row in rows} == {
        "regional_employment_to_population_ratio",
        "regional_unemployment_rate_oecd",
    }
    assert {row["unit"] for row in rows} == {"percent"}
    assert {row["value"] for row in rows} == {76.5, 77.2, 4.0, 4.2}


def test_sync_labour_writes_oecd_tl2_rows(monkeypatch):
    stored = []
    monkeypatch.setattr(
        module,
        "upsert_subnational_observations",
        lambda rows: stored.extend(rows) or len(rows),
    )

    adapter = OECDRegionalAdapter(client=None)
    monkeypatch.setattr(
        adapter,
        "fetch_labour",
        lambda **kwargs: LABOUR_CSV,
    )

    try:
        result = adapter.sync_labour(
            allowed_country_iso3={"AUS"},
            start_year=2021,
        )
    finally:
        adapter.close()

    assert result["rows"] == 4
    assert result["country_count"] == 1
    assert result["geography_count"] == 2
    assert result["geo_levels"] == ["tl2"]
    assert result["indicator_ids"] == [
        "regional_employment_to_population_ratio",
        "regional_unemployment_rate_oecd",
    ]


def test_fetch_labour_default_uses_validated_employment_ratio_key():
    class Response:
        text = LABOUR_CSV

        def raise_for_status(self):
            return None

    class Client:
        def __init__(self):
            self.calls = []

        def get(self, url, params):
            self.calls.append((url, params))
            return Response()

    client = Client()
    adapter = OECDRegionalAdapter(client=client)

    result = adapter.fetch_labour(start_year=2021)

    assert result == LABOUR_CSV
    assert client.calls[0][0].endswith(
        "/A.TL2+TL3...EMP_RATIO+UNE_RATE.Y15T64._T."
    )
    assert client.calls[0][1]["startPeriod"] == "2021"
