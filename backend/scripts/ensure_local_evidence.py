from __future__ import annotations

import json

import httpx

from app.db.bootstrap import initialize_datastores
from app.catalog import COUNTRIES
from app.core.config import settings
from app.db.analytics import (
    labour_oja_imbalance_eu27_status,
    labour_shortage_index_status,
    regional_sector_employment_status,
    environmental_health_burden_status,
    subnational_evidence_by_level_status,
    upsert_labour_oja_imbalance_eu27,
    upsert_labour_shortage_index,
    upsert_regional_sector_employment,
    upsert_environmental_health_burden,
)
from app.ingestion.eurostat import EurostatAdapter
from app.ingestion.eurostat_regional_sector import (
    fetch_regional_sector_employment,
)
from app.ingestion.eea_health_burden import fetch_eea_pm25_burden_evidence
from app.ingestion.cedefop_clssi import (
    download_workbook as download_clssi_workbook,
    parse_workbook as parse_clssi_workbook,
)
from app.ingestion.cedefop_oja_imbalance import (
    download_csv as download_oja_imbalance_csv,
    parse_csv as parse_oja_imbalance_csv,
)
from app.services.regional_evidence import sync_regional_evidence_codes


NUTS3_URL = (
    "https://gisco-services.ec.europa.eu/distribution/v2/nuts/geojson/"
    "NUTS_RG_20M_2024_4326_LEVL_3.geojson"
)


def ensure_eea_environmental_health_evidence() -> dict:
    before = environmental_health_burden_status()
    if before.get("available"):
        return {
            "evidence_id": "eea_environmental_health",
            "status": "available",
            "action": "none",
            "before": before,
            "after": before,
        }

    prefixes = {
        country["iso2"]
        for country in COUNTRIES
        if country.get("eu_member")
    }
    rows, diagnostic = fetch_eea_pm25_burden_evidence(
        country_prefixes=prefixes,
    )
    rows_upserted = upsert_environmental_health_burden(rows)
    after = environmental_health_burden_status()

    return {
        "evidence_id": "eea_environmental_health",
        "status": "available" if after.get("available") else "missing",
        "action": "repaired" if after.get("available") else "repair_failed",
        "rows_parsed": len(rows),
        "rows_upserted": rows_upserted,
        "diagnostic": diagnostic,
        "before": before,
        "after": after,
    }


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
    target_iso2 = {
        country["iso2"]
        for country in COUNTRIES
        if country.get("eu_member")
    }
    available_prefixes = set(before.get("country_prefixes") or [])
    missing_prefixes = target_iso2 - available_prefixes

    if before.get("available") and not missing_prefixes:
        return {
            "evidence_id": "nuts3_safety",
            "status": "available",
            "action": "none",
            "before": before,
            "after": before,
            "missing_country_prefixes": [],
        }

    with httpx.Client(
        timeout=120,
        follow_redirects=True,
        headers={"User-Agent": "AUGUR/0.1"},
    ) as client:
        response = client.get(NUTS3_URL)
        response.raise_for_status()
        payload = response.json()

    requested_prefixes = missing_prefixes or target_iso2
    codes = sorted({
        str(feature.get("properties", {}).get("NUTS_ID", "")).upper()
        for feature in payload.get("features", [])
        if feature.get("properties", {}).get("CNTR_CODE") in requested_prefixes
        and len(str(feature.get("properties", {}).get("NUTS_ID", ""))) == 5
    })

    sync_result = sync_regional_evidence_codes(codes)
    after = subnational_evidence_by_level_status()["NUTS3"]

    return {
        "evidence_id": "nuts3_safety",
        "status": "available" if after.get("available") else "missing",
        "action": "repaired" if after.get("available") else "repair_failed",
        "region_count_requested": len(codes),
        "requested_country_prefixes": sorted(requested_prefixes),
        "missing_country_prefixes_before": sorted(missing_prefixes),
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


def ensure_oja_imbalance_evidence() -> dict:
    before = labour_oja_imbalance_eu27_status()
    if before.get("available"):
        return {
            "evidence_id": "cedefop_oja_imbalance",
            "status": "available",
            "action": "none",
            "before": before,
            "after": before,
        }

    path = (
        settings.data_dir
        / "cache"
        / "cedefop-oja-imbalance-2026-05.csv"
    )
    download = download_oja_imbalance_csv(path)
    rows = parse_oja_imbalance_csv(path)
    rows_upserted = upsert_labour_oja_imbalance_eu27(rows)
    after = labour_oja_imbalance_eu27_status()

    return {
        "evidence_id": "cedefop_oja_imbalance",
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
        ensure_eea_environmental_health_evidence(),
        ensure_clssi_evidence(),
        ensure_oja_imbalance_evidence(),
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
