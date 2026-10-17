"""Source-to-app read-through acceptance using an ephemeral DuckDB, never production.

This proves value/provenance preservation and conservative public API behavior.
It intentionally DOES NOT certify historical NUTS vintage or Eurostat quality flags.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

import duckdb
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.db import analytics
from app.api.routes import router
from app.services import regional_rankings as ranking_module


def verify(reference_path: Path) -> dict:
    source = duckdb.connect(str(reference_path), read_only=True)
    try:
        source_rows = source.execute("""
            SELECT country_iso3, geo_code, indicator_id, period, value,
                   unit, source_id, dataset_id, source_dimensions_json,
                   source_status, source_updated_at, retrieved_at
            FROM reference_observations
            ORDER BY geo_code, indicator_id
        """).fetchall()
    finally:
        source.close()
    if len(source_rows) != 62:
        raise ValueError(f"Unexpected official reference size: {len(source_rows)}")

    with TemporaryDirectory(prefix="augur-reference-e2e-") as directory:
        ephemeral_db = Path(directory) / "app_evidence.duckdb"
        settings = SimpleNamespace(duckdb_path=ephemeral_db)
        with patch.object(analytics, "settings", settings), patch.object(ranking_module, "settings", settings):
            analytics.initialize_analytics_schema()
            transformed = []
            for (country, geo, indicator, period, value, unit, provider, dataset,
                 dimensions, status, updated, retrieved) in source_rows:
                transformed.append({
                    "geo_code": geo, "geo_name": geo, "geo_level": "NUTS2",
                    "geography_system": "NUTS_UNSPECIFIED", "country_iso3": country,
                    "indicator_id": indicator, "period": period, "value": value,
                    "unit": unit, "source_id": provider, "dataset_id": dataset,
                    "retrieved_at": datetime.fromisoformat(retrieved),
                    "source_updated_at": updated, "response_dimensions_json": dimensions,
                    "source_observation_status": status,
                })
            inserted = analytics.upsert_subnational_observations(transformed)
            if inserted != len(source_rows):
                raise ValueError(f"Application ingestion count mismatch: {inserted}")

            actual = duckdb.connect(str(ephemeral_db), read_only=True)
            try:
                app_rows = actual.execute("""
                    SELECT geo_code, indicator_id, period, value, unit, source_id,
                           dataset_id, response_dimensions_json, source_observation_status
                    FROM subnational_observations
                    ORDER BY geo_code, indicator_id
                """).fetchall()
                registry_count = actual.execute("SELECT count(*) FROM geography_registry").fetchone()[0]
            finally:
                actual.close()
            expected = [(geo, indicator, period, value, unit, provider, dataset, dimensions, status)
                        for (_country, geo, indicator, period, value, unit, provider, dataset,
                             dimensions, status, _updated, _retrieved) in source_rows]
            if app_rows != expected:
                raise ValueError("Official-source values/provenance differ from persisted app evidence")
            for geo in sorted({item[1] for item in source_rows}):
                stored = analytics.latest_subnational_observations(geo, geography_system="NUTS_UNSPECIFIED")
                if len(stored) != 2:
                    raise ValueError(f"Application service read-through failed: {geo}")

            app = FastAPI()
            app.include_router(router, prefix="/api")
            response = TestClient(app).get("/api/rankings/regions",
                params={"indicator_id":"regional_employment_rate", "countries":"ESP,PRT,IRL"})
            if response.status_code != 200:
                raise ValueError(f"Public ranking API failed: {response.status_code}")
            payload = response.json()
            if payload.get("items") or payload.get("eligible_total") or payload.get("status") != "blocked_unverified_evidence":
                raise ValueError("Ranking API exposed unverified NUTS observation vintage")
            if payload.get("unregistered_evidence_rows") != len(source_rows) // 2:
                raise ValueError("Public ranking API did not report unregistered employment evidence")
            if registry_count:
                raise ValueError("Reference import accidentally certified a geography registry")

    return {
        "status":"official_reference_to_app_verified_without_vintage_certification",
        "source_rows":len(source_rows),"app_rows":len(app_rows),
        "service_geographies":len({item[1] for item in source_rows}),
        "source_flag_counts":dict(sorted(Counter(str(row[9]) for row in source_rows if row[9]).items())),
        "registered_geographies":registry_count,
        "ranking_api_status":payload.get("status"),
        "ranking_api_exposed_items":len(payload.get("items",[])),
        "production_writes":0,"ephemeral_app_db_removed":True,
        "quality_certified":False,"boundary_vintage_certified":False,
    }


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--reference-db",required=True,type=Path)
    parser.add_argument("--report",required=True,type=Path)
    args=parser.parse_args()
    result=verify(args.reference_db)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result))


if __name__=="__main__":
    main()
