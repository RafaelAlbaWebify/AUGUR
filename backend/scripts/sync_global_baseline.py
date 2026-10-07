from __future__ import annotations

import json

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

    try:
        countries = world_bank.register_country_catalog()
        codes = sorted(country["iso3"] for country in countries)

        print(f"Discovered {len(codes)} real countries from World Bank metadata.")

        print("\n[World Bank baseline]")
        wb_result = world_bank.sync_countries(codes)

        print("\n[IMF baseline]")
        imf_result = imf.sync_countries(codes)

        print("\n[UN WPP baseline]")
        wpp_csv = un_wpp.fetch_csv()
        wpp_result = un_wpp.sync_countries(codes, csv_text=wpp_csv)
    finally:
        world_bank.close()
        imf.close()
        un_wpp.close()

    coverage = country_coverage_summary()
    payload = {
        "country_catalog_count": len(codes),
        "analyzable_country_count": coverage["analyzable_country_count"],
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
