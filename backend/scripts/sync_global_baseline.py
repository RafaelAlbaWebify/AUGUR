from __future__ import annotations

import json
import argparse
from pathlib import Path
from time import perf_counter

from app.db.bootstrap import initialize_datastores
from app.ingestion.imf import IMFAdapter
from app.ingestion.imf_weo_official import OfficialWEOAdapter
from app.ingestion.un_wpp import UNWPPAdapter
from app.ingestion.world_bank import WorldBankAdapter
from app.services.country import country_coverage_summary


def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument("--imf-official-weo",action="store_true",help="Opt in to official October 2026 WEO; not for production remediation")
    parser.add_argument("--report",type=Path,help="Save versioned source-coverage acceptance JSON (public data only)")
    args=parser.parse_args()
    initialize_datastores()

    world_bank = WorldBankAdapter(timeout_seconds=120, max_retries=3)
    imf = OfficialWEOAdapter() if args.imf_official_weo else IMFAdapter(timeout_seconds=120, max_retries=3)
    un_wpp = UNWPPAdapter(timeout_seconds=180, max_retries=3)

    started_at = perf_counter()
    try:
        catalog_started = perf_counter()
        countries = world_bank.register_country_catalog()
        catalog_seconds = perf_counter() - catalog_started
        codes = sorted(country["iso3"] for country in countries)

        print(f"Discovered {len(codes)} real countries from World Bank metadata.")

        print("\n[World Bank baseline]")
        wb_started = perf_counter()
        wb_result = world_bank.sync_countries(codes)
        wb_seconds = perf_counter() - wb_started

        print("\n[IMF baseline]")
        imf_started = perf_counter()
        imf_result = (imf.sync_countries(codes, persist=True)
                      if args.imf_official_weo else imf.sync_countries(codes))
        imf_seconds = perf_counter() - imf_started

        print("\n[UN WPP baseline]")
        wpp_started = perf_counter()
        wpp_csv = un_wpp.fetch_csv()
        wpp_result = un_wpp.sync_countries(codes, csv_text=wpp_csv)
        wpp_seconds = perf_counter() - wpp_started
    finally:
        world_bank.close()
        imf.close()
        un_wpp.close()

    coverage = country_coverage_summary()
    payload = {
        "country_catalog_count": len(codes),
        "analyzable_country_count": coverage["analyzable_country_count"],
        "duration_seconds": {
            "country_catalog": round(catalog_seconds, 3),
            "world_bank": round(wb_seconds, 3),
            "imf": round(imf_seconds, 3),
            "un_wpp": round(wpp_seconds, 3),
            "total": round(perf_counter() - started_at, 3),
        },
        "sources": {
            "WORLD_BANK": {
                "rows": wb_result["rows"],
                "complete": wb_result["complete"],
                "failure_count": len(wb_result["failures"]),
            },
            "IMF": {
                "rows": imf_result["rows"],
                "complete": imf_result["complete"],
                "failure_count": len(imf_result["failures"]),
                "availability": "complete" if imf_result["complete"] else "unavailable" if imf_result["rows"] == 0 else "partial",
                "vintage": imf_result.get("vintage"),
                "source_contract": imf_result.get("source_contract") if args.imf_official_weo else None,
            },
            "UN_WPP": {
                "rows": wpp_result["rows"],
                "complete": wpp_result["complete"],
                "countries_with_data": wpp_result["countries_with_data"],
                "missing_country_iso3": wpp_result["missing_country_iso3"],
            },
        },
    }
    payload["acceptance"] = {
        "schema_version": 1,
        "status": "passed_with_source_gaps" if coverage["analyzable_country_count"] > 0 else "blocked",
        "production_database_certified": False,
        "rankings_certified": False,
        "operator_production_writes": 0,
        "source_gaps": {
            "imf_blocked_indicators": imf_result.get("source_contract", {}).get("blocked_indicator_ids", []) if args.imf_official_weo else [],
            "imf_series_missing_actual_metadata": imf_result.get("source_contract", {}).get("missing_latest_actual_series") if args.imf_official_weo else None,
            "un_wpp_missing_countries": wpp_result["missing_country_iso3"],
        },
    }
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(payload, indent=2, default=str) + chr(10), encoding="utf-8")
    print(json.dumps(payload, indent=2, default=str))

    # Global coverage is expected to be heterogeneous. The command succeeds
    # when it produces analyzable countries, while per-source gaps remain
    # explicit in the summary.
    return 0 if coverage["analyzable_country_count"] > 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
