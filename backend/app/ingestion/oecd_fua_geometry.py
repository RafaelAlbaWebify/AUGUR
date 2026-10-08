from __future__ import annotations

import io
import json
import re
import zipfile
from datetime import datetime, timezone

import httpx
import shapefile

from app.db.analytics import (
    geographies_for_country,
    upsert_geography_geometries,
)


CITY_BOUNDARIES_URL = (
    "https://www.oecd.org/content/dam/oecd/en/data/datasets/"
    "oecd-definition-of-cities-and-functional-urban-areas/"
    "cities%20%284%29.zip"
)
FUA_BOUNDARIES_URL = (
    "https://www.oecd.org/content/dam/oecd/en/data/datasets/"
    "oecd-definition-of-cities-and-functional-urban-areas/"
    "fuas%20%281%29.zip"
)
GEOGRAPHY_SYSTEM = "OECD_FUA"
SOURCE_ID = "OECD"
GEOMETRY_DATASET_VERSION = "official-boundaries-2026"
CODE_PATTERN = re.compile(r"^[A-Z]{2,3}\d{2,3}[CF]$")


class GeometrySourceRestricted(RuntimeError):
    pass


def _read_shapefile_archive(payload: bytes) -> tuple[shapefile.Reader, str]:
    archive = zipfile.ZipFile(io.BytesIO(payload))
    members = archive.namelist()

    shp_name = next(
        (name for name in members if name.lower().endswith(".shp")),
        None,
    )
    if shp_name is None:
        raise ValueError("OECD geometry archive contains no .shp file")

    stem = shp_name[:-4]
    member_lookup = {name.lower(): name for name in members}
    shx_name = member_lookup.get(f"{stem}.shx".lower())
    dbf_name = member_lookup.get(f"{stem}.dbf".lower())
    prj_name = member_lookup.get(f"{stem}.prj".lower())

    if not shx_name or not dbf_name:
        raise ValueError("OECD geometry archive is missing SHX/DBF companions")
    if not prj_name:
        raise ValueError("OECD geometry archive is missing projection metadata")

    projection = archive.read(prj_name).decode("utf-8", errors="replace")
    normalized = projection.upper().replace("_", " ")
    if not (
        "WGS 1984" in normalized
        or "WGS 84" in normalized
        or "EPSG","4326" in normalized
        or "EPSG:4326" in normalized
    ):
        raise ValueError(
            "OECD geometry archive projection is not verified as WGS84/EPSG:4326"
        )

    reader = shapefile.Reader(
        shp=io.BytesIO(archive.read(shp_name)),
        shx=io.BytesIO(archive.read(shx_name)),
        dbf=io.BytesIO(archive.read(dbf_name)),
    )
    return reader, projection


def _candidate_codes(record: dict) -> list[str]:
    candidates = []
    for value in record.values():
        if not isinstance(value, str):
            continue
        token = value.strip().upper()
        if CODE_PATTERN.fullmatch(token):
            candidates.append(token)
    return candidates


def geometry_rows_from_archive(
    payload: bytes,
    *,
    registered_geographies: list[dict],
    expected_level: str,
) -> list[dict]:
    reader, _projection = _read_shapefile_archive(payload)
    fields = [field[0] for field in reader.fields[1:]]

    registry = {
        str(item["source_geo_code"]).upper(): item
        for item in registered_geographies
        if (
            str(item.get("geography_system") or "").upper() == GEOGRAPHY_SYSTEM
            and str(item.get("geo_level") or "").lower() == expected_level.lower()
        )
    }
    if not registry:
        return []

    rows = []
    matched = set()
    for shape_record in reader.iterShapeRecords():
        record = dict(zip(fields, list(shape_record.record)))
        code = next(
            (
                candidate
                for candidate in _candidate_codes(record)
                if candidate in registry
            ),
            None,
        )
        if code is None:
            continue

        shape = shape_record.shape
        geometry = shape.__geo_interface__
        if not geometry or geometry.get("type") not in {
            "Polygon",
            "MultiPolygon",
        }:
            continue

        item = registry[code]
        bbox = list(shape.bbox)
        if len(bbox) != 4:
            continue

        rows.append({
            "geo_id": item["geo_id"],
            "country_iso3": item.get("country_iso3"),
            "geography_system": GEOGRAPHY_SYSTEM,
            "geo_level": expected_level.lower(),
            "source_geo_code": code,
            "geometry_geojson": json.dumps(
                geometry,
                separators=(",", ":"),
            ),
            "bbox_min_lon": float(bbox[0]),
            "bbox_min_lat": float(bbox[1]),
            "bbox_max_lon": float(bbox[2]),
            "bbox_max_lat": float(bbox[3]),
            "source_id": SOURCE_ID,
            "dataset_version": GEOMETRY_DATASET_VERSION,
            "retrieved_at": datetime.now(timezone.utc),
        })
        matched.add(code)

    return rows


def fetch_archive(
    url: str,
    *,
    client: httpx.Client,
) -> bytes:
    response = client.get(url)
    if response.status_code in {401, 403}:
        raise GeometrySourceRestricted(
            f"OECD geometry archive access restricted: HTTP {response.status_code}"
        )
    response.raise_for_status()
    return response.content


def sync_oecd_fua_geometries_for_countries(
    country_iso3s: list[str] | set[str],
    *,
    client: httpx.Client | None = None,
    city_payload: bytes | None = None,
    fua_payload: bytes | None = None,
) -> dict:
    countries = sorted({
        str(code).strip().upper()
        for code in country_iso3s
        if str(code).strip()
    })
    registered = []
    for code in countries:
        registered.extend(
            item
            for item in geographies_for_country(code)
            if str(item.get("geography_system") or "").upper() == GEOGRAPHY_SYSTEM
        )

    if not registered:
        return {
            "geography_system": GEOGRAPHY_SYSTEM,
            "target_country_count": len(countries),
            "status": "no_registered_oecd_urban_geographies",
            "rows": 0,
            "city_rows": 0,
            "fua_rows": 0,
            "covered_countries": [],
            "missing_countries": countries,
            "complete": False,
        }

    owns_client = client is None
    active_client = client or httpx.Client(
        timeout=httpx.Timeout(180.0),
        follow_redirects=True,
        headers={"User-Agent": "AUGUR/0.1"},
    )
    try:
        if city_payload is None:
            city_payload = fetch_archive(
                CITY_BOUNDARIES_URL,
                client=active_client,
            )
        if fua_payload is None:
            fua_payload = fetch_archive(
                FUA_BOUNDARIES_URL,
                client=active_client,
            )
    finally:
        if owns_client:
            active_client.close()

    city_rows = geometry_rows_from_archive(
        city_payload,
        registered_geographies=registered,
        expected_level="city",
    )
    fua_rows = geometry_rows_from_archive(
        fua_payload,
        registered_geographies=registered,
        expected_level="fua",
    )
    all_rows = city_rows + fua_rows
    stored = upsert_geography_geometries(all_rows)

    registry_country_by_geo_id = {
        item["geo_id"]: item.get("country_iso3")
        for item in registered
    }
    covered_countries = sorted({
        registry_country_by_geo_id.get(row["geo_id"])
        for row in all_rows
        if registry_country_by_geo_id.get(row["geo_id"])
    })
    missing_countries = sorted(set(countries) - set(covered_countries))

    expected_codes = {
        str(item["source_geo_code"]).upper()
        for item in registered
    }
    matched_codes = {
        row["source_geo_code"]
        for row in all_rows
    }

    return {
        "geography_system": GEOGRAPHY_SYSTEM,
        "target_country_count": len(countries),
        "status": "available" if all_rows else "no_matching_geometry",
        "rows": stored,
        "city_rows": len(city_rows),
        "fua_rows": len(fua_rows),
        "covered_countries": covered_countries,
        "missing_countries": missing_countries,
        "missing_geo_codes": sorted(expected_codes - matched_codes),
        "complete": bool(all_rows) and expected_codes <= matched_codes,
    }


def sync_oecd_fua_geometries(
    country_iso3: str,
    *,
    client: httpx.Client | None = None,
    city_payload: bytes | None = None,
    fua_payload: bytes | None = None,
) -> dict:
    code = country_iso3.upper()
    registered = geographies_for_country(code)
    oecd_registered = [
        item
        for item in registered
        if str(item.get("geography_system") or "").upper() == GEOGRAPHY_SYSTEM
    ]

    if not oecd_registered:
        return {
            "country_iso3": code,
            "geography_system": GEOGRAPHY_SYSTEM,
            "status": "no_registered_oecd_urban_geographies",
            "rows": 0,
            "city_rows": 0,
            "fua_rows": 0,
        }

    owns_client = client is None
    active_client = client or httpx.Client(
        timeout=httpx.Timeout(180.0),
        follow_redirects=True,
        headers={"User-Agent": "AUGUR/0.1"},
    )
    try:
        if city_payload is None:
            city_payload = fetch_archive(
                CITY_BOUNDARIES_URL,
                client=active_client,
            )
        if fua_payload is None:
            fua_payload = fetch_archive(
                FUA_BOUNDARIES_URL,
                client=active_client,
            )
    finally:
        if owns_client:
            active_client.close()

    city_rows = geometry_rows_from_archive(
        city_payload,
        registered_geographies=oecd_registered,
        expected_level="city",
    )
    fua_rows = geometry_rows_from_archive(
        fua_payload,
        registered_geographies=oecd_registered,
        expected_level="fua",
    )
    all_rows = city_rows + fua_rows
    stored = upsert_geography_geometries(all_rows)

    expected_city_codes = {
        item["source_geo_code"]
        for item in oecd_registered
        if str(item.get("geo_level") or "").lower() == "city"
    }
    expected_fua_codes = {
        item["source_geo_code"]
        for item in oecd_registered
        if str(item.get("geo_level") or "").lower() == "fua"
    }
    matched_city_codes = {row["source_geo_code"] for row in city_rows}
    matched_fua_codes = {row["source_geo_code"] for row in fua_rows}

    return {
        "country_iso3": code,
        "geography_system": GEOGRAPHY_SYSTEM,
        "status": "available" if all_rows else "no_matching_geometry",
        "rows": stored,
        "city_rows": len(city_rows),
        "fua_rows": len(fua_rows),
        "missing_city_codes": sorted(expected_city_codes - matched_city_codes),
        "missing_fua_codes": sorted(expected_fua_codes - matched_fua_codes),
        "complete": (
            bool(all_rows)
            and expected_city_codes <= matched_city_codes
            and expected_fua_codes <= matched_fua_codes
        ),
    }
