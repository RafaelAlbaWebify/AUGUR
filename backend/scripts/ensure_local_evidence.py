from __future__ import annotations

import json

import httpx

from app.db.bootstrap import initialize_datastores
from app.catalog import COUNTRIES
from app.db.analytics import (
    labour_shortage_index_status,
    regional_sector_employment_status,
    subnational_evidence_by_level_status,
    upsert_labour_shortage_index,
    upsert_regional_sector_employment,
)
from app.ingestion.eurostat import EurostatAdapter
from app.ingestion.eurostat_regional_sector import (
    fetch_regional_sector_employment,
)
from app.ingestion.cedefop_clssi import (
    download_workbook as download_clssi_workbook,
    parse_workbook as parse_clssi_workbook,
)
from app.services.regional_evidence import sync_regional_evidence_codes


NUTS3_URL = (
    "https://gisco-services.ec.europa.eu/distribution/v2/nuts/geojson/"
    "NUTS_RG_20M_2024_4326_LEVL_3.geojson"
)


def ensure_regional_sector_evidence() -> dict:
    before = regional_sector_employment_status()
    if before.get("available"):
        return {
            "evidence_id": "regional_sector_employment",
            "status": "available",
            "action": "none",
            "before": before,
            "after": before,
        }

    adapter = EurostatAdapter(timeout_seconds=120, max_retries=3)
    try:
        rows, diagnostic = fetch_regional_sector_employment(adapter)
    finally:
        adapter.close()

    rows_upserted = upsert_regional_sector_employment(rows)
    after = regional_sector_employment_status()

    return {
        "evidence_id": "regional_sector_employment",
        "status": "available" if after.get("available") else "missing",
        "action": "repaired" if after.get("available") else "repair_failed",
        "rows_parsed": len(rows),
        "rows_upserted": rows_upserted,
        "diagnostic": diagnostic,
        "before": before,
        "after": after,
    }


def ensure_nuts3_safety_evidence() -> dict:
    before = subnational_evidence_by_level_status()["NUTS3"]
    if before.get("available"):
        return {
            "evidence_id": "nuts3_safety",
            "status": "available",
            "action": "none",
            "before": before,
            "after": before,
        }

    target_iso2 = {
        country["iso2"]
        for country in COUNTRIES
        if country.get("eu_member")
    }

    with httpx.Client(
        timeout=120,
        follow_redirects=True,
        headers={"User-Agent": "AUGUR/0.1"},
    ) as client:
        response = client.get(NUTS3_URL)
        response.raise_for_status()
        payload = response.json()

    codes = sorted({
        str(feature.get("properties", {}).get("NUTS_ID", "")).upper()
        for feature in payload.get("features", [])
        if feature.get("properties", {}).get("CNTR_CODE") in target_iso2
        and len(str(feature.get("properties", {}).get("NUTS_ID", ""))) == 5
    })

    sync_result = sync_regional_evidence_codes(codes)
    after = subnational_evidence_by_level_status()["NUTS3"]

    return {
        "evidence_id": "nuts3_safety",
        "status": "available" if after.get("available") else "missing",
        "action": "repaired" if after.get("available") else "repair_failed",
        "region_count_requested": len(codes),
        "sync_result": sync_result,
        "before": before,
        "after": after,
    }


def ensure_clssi_evidence() -> dict:
    before = labour_shortage_index_status()
    if before.get("available"):
        return {
            "evidence_id": "cedefop_clssi",
            "status": "available",
            "action": "none",
            "before": before,
            "after": before,
        }

    from app.core.config import settings

    path = settings.data_dir / "cache" / "cedefop_clssi_2026.xlsx"
    download = download_clssi_workbook(path)
    rows = parse_clssi_workbook(path)
    rows_upserted = upsert_labour_shortage_index(rows)
    after = labour_shortage_index_status()

    return {
        "evidence_id": "cedefop_clssi",
        "status": "available" if after.get("available") else "missing",
        "action": "repaired" if after.get("available") else "repair_failed",
        "rows_parsed": len(rows),
        "rows_upserted": rows_upserted,
        "download": download,
        "before": before,
        "after": after,
    }


def main() -> int:
    initialize_datastores()

    results = [
        ensure_regional_sector_evidence(),
        ensure_nuts3_safety_evidence(),
        ensure_clssi_evidence(),
    ]
    repaired = [
        item["evidence_id"]
        for item in results
        if item["action"] == "repaired"
    ]
    failed = [
        item["evidence_id"]
        for item in results
        if item["status"] != "available"
    ]

    payload = {
        "status": "complete" if not failed else "partial",
        "repaired": repaired,
        "failed": failed,
        "results": results,
    }
    print(json.dumps(payload, indent=2, default=str))
    return 0 if not failed else 2


if __name__ == "__main__":
    raise SystemExit(main())
