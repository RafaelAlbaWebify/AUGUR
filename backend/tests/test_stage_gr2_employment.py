import duckdb
import pytest
from scripts.stage_gr2_employment import stage, fingerprint


class Source:
    def fetch_dataset(self, dataset_id, filters):
        return {"dataset": dataset_id, "filters": filters}

    def normalize(self, country, config, payload):
        assert config["dimension_values"] == payload["filters"]
        return [
            {"period": 2025, "value": 72.5,
             "source_dimensions": {**payload["filters"], "geo": code},
             "source_observation_status": "d", "source_updated_at": "2026-09-10"}
            for code in payload["filters"]["geo"]
        ]


def fixture_db(tmp_path):
    source = tmp_path / "original.duckdb"
    con = duckdb.connect(str(source))
    con.execute("""CREATE TABLE geography_registry
        (source_geo_code VARCHAR, country_iso3 VARCHAR, geography_system VARCHAR, geo_level VARCHAR)""")
    con.execute("""CREATE TABLE subnational_observations (
        geography_system VARCHAR, geo_code VARCHAR, geo_level VARCHAR,
        indicator_id VARCHAR, period INTEGER, value DOUBLE,
        request_filters_json VARCHAR, response_dimensions_json VARCHAR,
        source_observation_status VARCHAR, source_updated_at VARCHAR)""")
    con.execute("""INSERT INTO geography_registry VALUES ('ES11','ESP','NUTS_2024','nuts2')""")
    con.execute("""INSERT INTO subnational_observations VALUES
        ('NUTS_2024','ES11','nuts2','regional_employment_rate',2025,67.4,NULL,NULL,NULL,NULL)""")
    con.close()
    return source


def test_staging_only_writes_new_copy_and_retains_before_image(tmp_path):
    source = fixture_db(tmp_path)
    before = fingerprint(source)
    stage_path = tmp_path / "candidate.duckdb"
    result = stage(source, stage_path, Source())
    assert result["changed_rows"] == 1
    assert result["source_unchanged"]
    assert result["production_writes"] == 0
    assert result["flag_counts"] == {"d": 1}
    assert fingerprint(source) == before
    con = duckdb.connect(str(source), read_only=True)
    assert con.execute("SELECT value FROM subnational_observations").fetchone()[0] == 67.4
    con.close()
    con = duckdb.connect(str(stage_path), read_only=True)
    assert con.execute("SELECT value FROM subnational_observations").fetchone()[0] == 72.5
    assert con.execute("SELECT value FROM gr2_remediation_before").fetchone()[0] == 67.4
    con.close()
    with pytest.raises(FileExistsError):
        stage(source, stage_path, Source())
    assert fingerprint(source) == before


class Duplicate(Source):
    def normalize(self, country, config, payload):
        return super().normalize(country, config, payload) * 2


def test_ambiguous_provider_never_creates_staged_database(tmp_path):
    source = fixture_db(tmp_path)
    stage_path = tmp_path / "candidate.duckdb"
    with pytest.raises(ValueError, match="Duplicate"):
        stage(source, stage_path, Duplicate())
    assert not stage_path.exists()
