from __future__ import annotations

import csv
import io
import zipfile

import httpx


DATASET_ID = "EEA_PM25_PREMATURE_DEATHS_NUTS23"
DATASET_VERSION = "eea_s_eu-sdg-nuts23-11-52_p_2005-2023_v01_r00"
DATASET_PAGE_URL = "https://sdi.eea.europa.eu/data/9770b4f2-352e-4a0b-af80-c09ec7961b33"
DOWNLOAD_URL = "https://sdi.eea.europa.eu/datashare/s/zCSjC9WbwK4ejy2/download"


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


def inspect_eea_pm25_burden_dataset(
    client: httpx.Client | None = None,
) -> dict:
    owns_client = client is None
    active = client or httpx.Client(
        timeout=120,
        follow_redirects=True,
        headers={"User-Agent": "AUGUR/0.1 EEA health burden inspector"},
    )
    try:
        response = active.get(DOWNLOAD_URL)
        response.raise_for_status()
        payload = response.content
    finally:
        if owns_client:
            active.close()

    archive = zipfile.ZipFile(io.BytesIO(payload))
    members = [
        name
        for name in archive.namelist()
        if not name.endswith("/")
    ]
    tabular = [
        name
        for name in members
        if name.lower().endswith((".csv", ".txt"))
    ]

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
