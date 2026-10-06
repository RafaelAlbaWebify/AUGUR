from __future__ import annotations

import calendar
import csv
import io
import tempfile
from pathlib import Path

import duckdb
import httpx

from app.ingestion.eea_air_quality_api import (
    PM25_URI,
    probe_verified_pm25_city,
)


SOURCE_ID = "EEA"
DATASET_ID = "EEA_AIR_QUALITY_E1A_CITY_MEASUREMENTS"
INDICATOR_ID = "city_pm25_annual_mean_observed"
UNIT = "ug_m3"


def _urls_from_probe(probe: dict) -> list[str]:
    payload = probe.get("urls")
    if not isinstance(payload, dict):
        return []
    raw = payload.get("raw_text")
    if not isinstance(raw, str):
        return []

    reader = csv.DictReader(io.StringIO(raw.lstrip("\ufeff")))
    return [
        str(row.get("ParquetFileUrl") or "").strip()
        for row in reader
        if str(row.get("ParquetFileUrl") or "").strip().startswith("http")
    ]


def annual_record_threshold(agg_type: str, year: int) -> int | None:
    if agg_type == "hour":
        expected = (366 if calendar.isleap(year) else 365) * 24
    elif agg_type == "day":
        expected = 366 if calendar.isleap(year) else 365
    else:
        return None
    return int((expected * 0.75) + 0.999999999)


def select_eligible_station_means(
    streams: list[dict],
    year: int,
) -> tuple[list[dict], list[dict]]:
    by_station: dict[str, list[dict]] = {}
    excluded: list[dict] = []

    for stream in streams:
        agg_type = str(stream["agg_type"])
        threshold = annual_record_threshold(agg_type, year)
        enriched = {
            **stream,
            "required_records": threshold,
        }
        if threshold is None or int(stream["record_count"]) < threshold:
            excluded.append(enriched)
            continue
        by_station.setdefault(str(stream["sampling_point"]), []).append(
            enriched
        )

    selected: list[dict] = []
    preference = {"hour": 0, "day": 1}
    for station, candidates in by_station.items():
        best = min(
            candidates,
            key=lambda item: preference.get(str(item["agg_type"]), 99),
        )
        selected.append(best)
        for item in candidates:
            if item is not best:
                excluded.append({
                    **item,
                    "reason": "lower_preference_aggregation",
                })

    return selected, excluded


def aggregate_city_pm25_from_parquets(
    parquet_paths: list[Path],
    year: int,
) -> dict:
    if not parquet_paths:
        return {
            "status": "unavailable",
            "reason": "no_parquet_files",
            "year": year,
        }

    escaped = [
        "'" + str(path).replace("'", "''") + "'"
        for path in parquet_paths
    ]
    parquet_list = "[" + ", ".join(escaped) + "]"
    start = f"{year}-01-01 00:00:00"
    end = f"{year + 1}-01-01 00:00:00"

    con = duckdb.connect()
    try:
        result = con.execute(
            f"""
            WITH filtered AS (
                SELECT DISTINCT
                    Samplingpoint,
                    Start,
                    "End",
                    CAST(Value AS DOUBLE) AS Value,
                    Unit,
                    AggType
                FROM read_parquet({parquet_list}, union_by_name=true)
                WHERE Pollutant = 6001
                  AND Start >= TIMESTAMP '{start}'
                  AND Start < TIMESTAMP '{end}'
                  AND Value IS NOT NULL
                  AND Unit = 'ug.m-3'
                  AND Validity = 1
                  AND Verification = 1
                  AND AggType IN ('hour', 'day')
            )
            SELECT
                Samplingpoint,
                AggType,
                COUNT(*) AS record_count,
                AVG(Value) AS annual_mean
            FROM filtered
            GROUP BY Samplingpoint, AggType
            ORDER BY Samplingpoint, AggType
            """
        )
        streams = [
            {
                "sampling_point": row[0],
                "agg_type": row[1],
                "record_count": int(row[2]),
                "annual_mean": float(row[3]),
            }
            for row in result.fetchall()
        ]
    finally:
        con.close()

    selected, excluded = select_eligible_station_means(streams, year)
    if not selected:
        return {
            "status": "insufficient_coverage",
            "year": year,
            "eligible_sampling_point_count": 0,
            "streams": streams,
            "excluded_streams": excluded,
        }

    city_mean = sum(
        item["annual_mean"] for item in selected
    ) / len(selected)

    return {
        "status": "available",
        "year": year,
        "value": round(city_mean, 4),
        "unit": UNIT,
        "eligible_sampling_point_count": len(selected),
        "sampling_points": selected,
        "excluded_streams": excluded,
        "method": "arithmetic_mean_of_eligible_sampling_point_annual_means",
        "coverage_rule": "minimum_75_percent_calendar_year_records",
    }


def fetch_city_pm25_annual(
    city_name: str,
    country_code: str,
    year: int,
    client: httpx.Client | None = None,
) -> dict:
    owns_client = client is None
    active = client or httpx.Client(
        timeout=120,
        follow_redirects=True,
        headers={"User-Agent": "AUGUR/0.1 EEA city PM2.5"},
    )
    try:
        probe = probe_verified_pm25_city(
            city_name,
            country_code,
            year,
            client=active,
        )
        urls = _urls_from_probe(probe)
        if not urls:
            return {
                "status": "unavailable",
                "reason": "no_verified_pm25_files",
                "city_name": city_name,
                "country_code": country_code,
                "year": year,
            }

        with tempfile.TemporaryDirectory() as tmp:
            paths: list[Path] = []
            for index, url in enumerate(urls):
                response = active.get(url)
                response.raise_for_status()
                path = Path(tmp) / f"source_{index}.parquet"
                path.write_bytes(response.content)
                paths.append(path)

            aggregation = aggregate_city_pm25_from_parquets(
                paths,
                year,
            )
    finally:
        if owns_client:
            active.close()

    return {
        **aggregation,
        "city_name": city_name,
        "country_code": country_code,
        "source_id": SOURCE_ID,
        "dataset_id": DATASET_ID,
        "indicator_id": INDICATOR_ID,
        "pollutant_uri": PM25_URI,
        "verified_dataset": "E1a",
        "parquet_file_count": len(urls),
    }
