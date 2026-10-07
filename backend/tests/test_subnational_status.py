from datetime import datetime, timezone
from types import SimpleNamespace

import duckdb

from app.db import analytics as module


def test_subnational_status_counts_nuts2_nuts3_and_city_case_insensitively(
    monkeypatch,
    tmp_path,
):
    path = tmp_path / "subnational.duckdb"
    con = duckdb.connect(str(path))
    try:
        con.execute(
            """
            CREATE TABLE subnational_observations (
                geo_code TEXT,
                geo_level TEXT,
                indicator_id TEXT,
                retrieved_at TIMESTAMP
            )
            """
        )
        now = datetime.now(timezone.utc)
        con.executemany(
            """
            INSERT INTO subnational_observations
            VALUES (?, ?, ?, ?)
            """,
            [
                ("ES12", "NUTS2", "regional_employment_rate", now),
                ("PT11", "nuts2", "regional_unemployment_rate", now),
                ("ES120", "NUTS3", "regional_robbery_rate", now),
                ("IE061", "nuts3", "regional_intentional_homicide_rate", now),
                ("ES013C", "city", "city_population", now),
                ("PT001C", "CITY", "city_population", now),
            ],
        )
    finally:
        con.close()

    monkeypatch.setattr(
        module,
        "settings",
        SimpleNamespace(duckdb_path=path),
    )

    overall = module.subnational_storage_status()
    by_level = module.subnational_evidence_by_level_status()

    assert overall == {
        "observation_count": 6,
        "geography_count": 6,
        "nuts2_count": 2,
        "nuts3_count": 2,
        "city_count": 2,
    }
    assert by_level["NUTS2"]["geography_count"] == 2
    assert by_level["NUTS3"]["geography_count"] == 2
    assert by_level["CITY"]["geography_count"] == 2
    assert by_level["NUTS3"]["indicator_ids"] == [
        "regional_intentional_homicide_rate",
        "regional_robbery_rate",
    ]
