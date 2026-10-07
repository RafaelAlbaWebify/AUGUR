from __future__ import annotations

import csv
import io
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import httpx


DATASET_ID = "EEA_PM25_PREMATURE_DEATHS_NUTS23"
DATASET_VERSION = "eea_s_eu-sdg-nuts23-11-52_p_2005-2023_v01_r00"
DATASET_PAGE_URL = "https://sdi.eea.europa.eu/data/9770b4f2-352e-4a0b-af80-c09ec7961b33"
DOWNLOAD_URL = "https://sdi.eea.europa.eu/datashare/s/zCSjC9WbwK4ejy2/download"
SUPPORTED_DIMENSIONS = {"PMD", "YLL"}


def _sample_delimited_file(
    archive: zipfile.ZipFile,
    member: str,
    max_rows: int = 5,
) -> dict:
    raw = archive.read(member)
    text = raw.decode("utf-8-sig", errors="replace")
    sample = text[:20000]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
        delimiter = dialect.delimiter
    except csv.Error:
        delimiter = ","

    reader = csv.reader(io.StringIO(text), delimiter=delimiter)
    rows = []
    for index, row in enumerate(reader):
        rows.append(row)
        if index >= max_rows:
            break

    return {
        "member": member,
        "delimiter": delimiter,
        "headers": rows[0] if rows else [],
        "sample_rows": rows[1:] if len(rows) > 1 else [],
        "byte_size": len(raw),
    }


def _tabular_members(archive: zipfile.ZipFile) -> list[str]:
    return [
        name
        for name in archive.namelist()
        if not name.endswith("/")
        and name.lower().endswith((".csv", ".txt"))
    ]


def _primary_csv_member(archive: zipfile.ZipFile) -> str:
    members = [
        name
        for name in archive.namelist()
        if name.lower().endswith(".csv")
    ]
    preferred = [
        name
        for name in members
        if Path(name).name == f"{DATASET_VERSION}.csv"
    ]
    if preferred:
        return preferred[0]
    if len(members) == 1:
        return members[0]
    raise ValueError("EEA health-burden archive does not contain one identifiable CSV")


def download_eea_pm25_burden_dataset(
    client: httpx.Client | None = None,
) -> bytes:
    owns_client = client is None
    active = client or httpx.Client(
        timeout=120,
        follow_redirects=True,
        headers={"User-Agent": "AUGUR/0.1 EEA health burden sync"},
    )
    try:
        response = active.get(DOWNLOAD_URL)
        response.raise_for_status()
        return response.content
    finally:
        if owns_client:
            active.close()


def parse_eea_pm25_burden_archive(
    payload: bytes,
    *,
    country_prefixes: set[str] | None = None,
    retrieved_at: datetime | None = None,
) -> list[dict]:
    prefixes = {
        value.strip().upper()
        for value in (country_prefixes or set())
        if value.strip()
    }
    retrieved = retrieved_at or datetime.now(timezone.utc)

    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        member = _primary_csv_member(archive)
        raw = archive.read(member).decode("utf-8-sig", errors="strict")

    reader = csv.DictReader(io.StringIO(raw))
    expected = {
        "code",
        "dimension",
        "dimension_label",
        "unit",
        "unit_label",
        "geo",
        "geo_label",
        "time",
        "obs_value",
        "obs_status",
    }
    missing = expected - set(reader.fieldnames or [])
    if missing:
        raise ValueError(
            "EEA health-burden CSV missing columns: "
            + ", ".join(sorted(missing))
        )

    rows: list[dict] = []
    for source in reader:
        dimension = (source.get("dimension") or "").strip().upper()
        geo_code = (source.get("geo") or "").strip().upper()
        unit_code = (source.get("unit") or "").strip().upper()
        value_text = (source.get("obs_value") or "").strip()
        period_text = (source.get("time") or "").strip()

        if dimension not in SUPPORTED_DIMENSIONS:
            continue
        if len(geo_code) not in {4, 5}:
            continue
        if prefixes and geo_code[:2] not in prefixes:
            continue
        if not value_text or not period_text:
            continue

        try:
            value = float(value_text)
            period = int(period_text)
        except ValueError:
            continue

        rows.append({
            "geo_code": geo_code,
            "geo_name": (source.get("geo_label") or "").strip() or None,
            "geo_level": "NUTS2" if len(geo_code) == 4 else "NUTS3",
            "period": period,
            "burden_type": dimension,
            "burden_label": (source.get("dimension_label") or "").strip() or dimension,
            "value": value,
            "unit_code": unit_code,
            "unit_label": (source.get("unit_label") or "").strip() or unit_code,
            "obs_status": (source.get("obs_status") or "").strip() or None,
            "source_id": "EEA",
            "dataset_id": DATASET_ID,
            "dataset_version": DATASET_VERSION,
            "retrieved_at": retrieved,
        })

    return rows


def fetch_eea_pm25_burden_evidence(
    *,
    country_prefixes: set[str] | None = None,
    client: httpx.Client | None = None,
) -> tuple[list[dict], dict]:
    payload = download_eea_pm25_burden_dataset(client=client)
    rows = parse_eea_pm25_burden_archive(
        payload,
        country_prefixes=country_prefixes,
    )
    diagnostic = {
        "dataset_id": DATASET_ID,
        "dataset_version": DATASET_VERSION,
        "download_bytes": len(payload),
        "row_count": len(rows),
        "geography_count": len({row["geo_code"] for row in rows}),
        "geo_levels": sorted({row["geo_level"] for row in rows}),
        "country_prefixes": sorted({row["geo_code"][:2] for row in rows}),
        "period_min": min((row["period"] for row in rows), default=None),
        "period_max": max((row["period"] for row in rows), default=None),
        "burden_types": sorted({row["burden_type"] for row in rows}),
        "unit_codes": sorted({row["unit_code"] for row in rows}),
    }
    return rows, diagnostic


def inspect_eea_pm25_burden_dataset(
    client: httpx.Client | None = None,
) -> dict:
    payload = download_eea_pm25_burden_dataset(client=client)

    archive = zipfile.ZipFile(io.BytesIO(payload))
    members = [
        name
        for name in archive.namelist()
        if not name.endswith("/")
    ]
    tabular = _tabular_members(archive)

    samples = [
        _sample_delimited_file(archive, member)
        for member in tabular[:6]
    ]

    return {
        "dataset_id": DATASET_ID,
        "dataset_version": DATASET_VERSION,
        "status": "available" if members else "empty",
        "dataset_page_url": DATASET_PAGE_URL,
        "download_url": DOWNLOAD_URL,
        "download_bytes": len(payload),
        "member_count": len(members),
        "members": members,
        "tabular_member_count": len(tabular),
        "tabular_samples": samples,
        "ready_for_parser_design": bool(tabular),
        "notes": [
            "Inspection is read-only; no EEA health-burden data are written to DuckDB.",
            "This dataset is health-impact evidence and must remain separate from observed city PM2.5 concentration measurements.",
            "AUGUR must preserve published NUTS2/NUTS3 granularity and observation year.",
        ],
    }
