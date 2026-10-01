from __future__ import annotations

import argparse

from app.catalog import COUNTRIES
from app.db.bootstrap import initialize_datastores
from app.ingestion.eurostat import EurostatAdapter
from app.ingestion.imf import IMFAdapter
from app.ingestion.oecd import OECDAdapter
from app.ingestion.un_wpp import UNWPPAdapter
from app.ingestion.world_bank import WorldBankAdapter


DEFAULT_COUNTRIES = ["ESP", "PRT", "IRL"]


def sync_country(
    country_iso3: str,
    world_bank: WorldBankAdapter,
    eurostat: EurostatAdapter,
    oecd: OECDAdapter,
    imf: IMFAdapter,
    un_wpp: UNWPPAdapter,
    un_csv: str,
) -> dict:
    print()
    print("=" * 72)
    print(f"AUGUR CORE SYNC · {country_iso3}")
    print("=" * 72)

    results = {}

    print()
    print("[World Bank]")
    results["WORLD_BANK"] = world_bank.sync_country(country_iso3)

    print()
    print("[Eurostat]")
    results["EUROSTAT"] = eurostat.sync_country(country_iso3)

    print()
    print("[OECD]")
    results["OECD"] = oecd.sync_country(country_iso3)

    print()
    print("[IMF]")
    results["IMF"] = imf.sync_country(country_iso3)

    print()
    print("[UN WPP]")
    results["UN_WPP"] = un_wpp.sync_country(country_iso3, csv_text=un_csv)

    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="Synchronize AUGUR core sources.")
    parser.add_argument(
        "--countries",
        nargs="+",
        default=DEFAULT_COUNTRIES,
        help="ISO3 country codes. Default: ESP PRT IRL",
    )
    args = parser.parse_args()

    registered = {country["iso3"] for country in COUNTRIES}
    countries = [value.upper() for value in args.countries]

    unknown = [code for code in countries if code not in registered]
    if unknown:
        raise SystemExit(f"Unsupported countries: {', '.join(unknown)}")

    initialize_datastores()

    world_bank = WorldBankAdapter(timeout_seconds=90, max_retries=3)
    eurostat = EurostatAdapter(timeout_seconds=90, max_retries=3)
    oecd = OECDAdapter(timeout_seconds=90, max_retries=3)
    imf = IMFAdapter(timeout_seconds=90, max_retries=3)
    un_wpp = UNWPPAdapter(timeout_seconds=120, max_retries=3)

    try:
        print("Downloading UN WPP bulk file once for this sync...")
        un_csv = un_wpp.fetch_csv()

        all_results = {}
        for country_iso3 in countries:
            all_results[country_iso3] = sync_country(
                country_iso3,
                world_bank,
                eurostat,
                oecd,
                imf,
                un_wpp,
                un_csv,
            )
    finally:
        world_bank.close()
        eurostat.close()
        oecd.close()
        imf.close()
        un_wpp.close()

    print()
    print("=" * 72)
    print("AUGUR CORE SYNC SUMMARY")
    print("=" * 72)

    complete = True

    for country_iso3, source_results in all_results.items():
        print(country_iso3)

        for source_id, result in source_results.items():
            source_complete = bool(result.get("complete", True))
            complete = complete and source_complete
            print(
                f"  {source_id:<12} rows={result.get('rows', 0):<5} "
                f"complete={source_complete}"
            )

    print()
    print("Complete:", complete)
    return 0 if complete else 2


if __name__ == "__main__":
    raise SystemExit(main())
