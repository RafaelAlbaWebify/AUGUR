from __future__ import annotations

import json
from time import perf_counter

from app.db.bootstrap import initialize_datastores
from app.ingestion.imf import IMFAdapter
from app.ingestion.un_wpp import UNWPPAdapter
from app.ingestion.world_bank import WorldBankAdapter
from app.services.country import country_coverage_summary


def main() -> int:
    initialize_datastores()

    world_bank = WorldBankAdapter(timeout_seconds=120, max_retries=3)
    imf = IMFAdapter(timeout_seconds=120, max_retries=3)
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
        imf_result = imf.sync_countries(codes)
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
            },
            "UN_WPP": {
                "rows": wpp_result["rows"],
                "complete": wpp_result["complete"],
                "countries_with_data": wpp_result["countries_with_data"],
            },
        },
    }
    print(json.dumps(payload, indent=2, default=str))

    # Global coverage is expected to be heterogeneous. The command succeeds
    # when it produces analyzable countries, while per-source gaps remain
    # explicit in the summary.
    return 0 if coverage["analyzable_country_count"] > 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
