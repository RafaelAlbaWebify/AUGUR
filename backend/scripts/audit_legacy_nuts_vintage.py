"""Read-only audit of legacy local NUTS_2024 claims against GISCO 2024.

This never rewrites or deletes observations. It can prove that a code is not a
member of the current NUTS 2024 catalog, but current code membership alone does
not prove the boundary vintage used by an historical observation.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import duckdb
import httpx

from app.core.config import settings

GISCO_URLS = {
    "nuts2": (
        "https://gisco-services.ec.europa.eu/distribution/v2/nuts/geojson/"
        "NUTS_RG_20M_2024_4326_LEVL_2.geojson"
    ),
    "nuts3": (
        "https://gisco-services.ec.europa.eu/distribution/v2/nuts/geojson/"
        "NUTS_RG_20M_2024_4326_LEVL_3.geojson"
    ),
}


def extract_codes(payload: dict, level: str) -> set[str]:
    expected_level = {"nuts2": "2", "nuts3": "3"}[level]
    if payload.get("type") != "FeatureCollection":
        raise ValueError(f"Invalid GISCO {level} FeatureCollection")
    features = payload.get("features")
    if not isinstance(features, list) or not features:
        raise ValueError(f"Empty GISCO {level} registry")

    codes: set[str] = set()
    for feature in features:
        props = feature.get("properties") or {}
        code = props.get("NUTS_ID")
        feature_level = str(props.get("LEVL_CODE"))
        if feature_level != expected_level:
            raise ValueError(f"Unexpected GISCO level in {level} registry")
        expected_length = 4 if level == "nuts2" else 5
        if not isinstance(code, str) or len(code) != expected_length:
            raise ValueError(f"Unexpected GISCO code in {level} registry")
        codes.add(code.upper())
    return codes


def fetch_official_codes() -> dict[str, set[str]]:
    with httpx.Client(
        timeout=120,
        follow_redirects=True,
        headers={"User-Agent": "AUGUR/0.1"},
    ) as client:
        result = {}
        for level, url in GISCO_URLS.items():
            response = client.get(url)
            response.raise_for_status()
            result[level] = extract_codes(response.json(), level)
    return result


def classify_claims(
    official: dict[str, set[str]],
    observations: list[dict],
    registry_rows: list[dict],
) -> dict:
    observation_results = []
    for row in observations:
        level = str(row.get("geo_level") or "").lower()
        code = str(row.get("geo_code") or "").upper()
        if level not in official:
            status = "unsupported_nuts_level"
        elif code not in official[level]:
            status = "not_in_nuts2024_registry"
        else:
            status = "code_current_observation_vintage_unverified"
        observation_results.append({**row, "audit_status": status})

    registry_results = []
    for row in registry_rows:
        level = str(row.get("geo_level") or "").lower()
        code = str(row.get("source_geo_code") or "").upper()
        if level not in official:
            status = "unsupported_nuts_level"
        elif code not in official[level]:
            status = "invalid_current_registry_membership"
        else:
            status = "current_registry_membership_confirmed"
        registry_results.append({**row, "audit_status": status})

    definite_observation_mislabels = [
        row for row in observation_results
        if row["audit_status"] == "not_in_nuts2024_registry"
    ]
    ambiguous_current_code_observations = [
        row for row in observation_results
        if row["audit_status"] == "code_current_observation_vintage_unverified"
    ]
    invalid_registry = [
        row for row in registry_results
        if row["audit_status"] == "invalid_current_registry_membership"
    ]

    return {
        "scope": "legacy_local_nuts2024_vintage_audit",
        "mutation_performed": False,
        "warning": (
            "A current NUTS 2024 code does not prove that an historical "
            "observation used 2024 boundaries. Codes absent from the official "
            "2024 registry cannot validly be claimed as NUTS_2024. This audit "
            "does not delete or rewrite local history."
        ),
        "summary": {
            "nuts2024_observation_groups": len(observation_results),
            "definite_observation_mislabels": len(definite_observation_mislabels),
            "current_code_vintage_unverified": len(ambiguous_current_code_observations),
            "nuts2024_registry_rows": len(registry_results),
            "invalid_current_registry_rows": len(invalid_registry),
        },
        "definite_observation_mislabels": definite_observation_mislabels,
        "current_code_vintage_unverified": ambiguous_current_code_observations,
        "invalid_current_registry_rows": invalid_registry,
        "registry_rows": registry_results,
    }


def load_local_claims(db_path: Path) -> tuple[list[dict], list[dict]]:
    if not db_path.exists():
        raise FileNotFoundError(f"DuckDB not found: {db_path}")
    con = duckdb.connect(str(db_path), read_only=True)
    try:
        tables = {
            row[0]
            for row in con.execute(
                "SELECT table_name FROM information_schema.tables"
            ).fetchall()
        }
        required = {"subnational_observations", "geography_registry"}
        missing = required - tables
        if missing:
            raise ValueError(
                "Local DuckDB is missing required tables: "
                + ", ".join(sorted(missing))
            )

        obs_result = con.execute(
            """
            SELECT
                LOWER(geo_level) AS geo_level,
                UPPER(geo_code) AS geo_code,
                source_id,
                dataset_id,
                MIN(period) AS first_period,
                MAX(period) AS last_period,
                COUNT(*) AS observation_count,
                MIN(retrieved_at) AS first_retrieved_at,
                MAX(retrieved_at) AS last_retrieved_at
            FROM subnational_observations
            WHERE UPPER(geography_system) = 'NUTS_2024'
              AND LOWER(geo_level) IN ('nuts2', 'nuts3')
            GROUP BY LOWER(geo_level), UPPER(geo_code), source_id, dataset_id
            ORDER BY LOWER(geo_level), UPPER(geo_code), source_id, dataset_id
            """
        )
        obs_columns = [item[0] for item in obs_result.description]
        observations = [
            dict(zip(obs_columns, row))
            for row in obs_result.fetchall()
        ]

        registry_result = con.execute(
            """
            SELECT
                geo_id,
                country_iso3,
                country_iso2,
                name,
                LOWER(geo_level) AS geo_level,
                geography_system,
                source_id,
                UPPER(source_geo_code) AS source_geo_code
            FROM geography_registry
            WHERE UPPER(geography_system) = 'NUTS_2024'
              AND LOWER(geo_level) IN ('nuts2', 'nuts3')
            ORDER BY LOWER(geo_level), UPPER(source_geo_code)
            """
        )
        registry_columns = [item[0] for item in registry_result.description]
        registry_rows = [
            dict(zip(registry_columns, row))
            for row in registry_result.fetchall()
        ]
        return observations, registry_rows
    finally:
        con.close()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Audit legacy local NUTS_2024 claims without changing data."
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=Path(settings.duckdb_path),
        help="AUGUR DuckDB path (defaults to configured analytical database).",
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    official = fetch_official_codes()
    observations, registry_rows = load_local_claims(args.db)
    report = classify_claims(official, observations, registry_rows)
    report["official_registry_counts"] = {
        level: len(codes)
        for level, codes in official.items()
    }
    report["database"] = str(args.db)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, default=str) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report["summary"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
