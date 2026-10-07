from __future__ import annotations

import json

from app.catalog import country_membership_flags
from app.ingestion.imf import IMFAdapter, SERIES as IMF_SERIES
from app.ingestion.un_wpp import UNWPPAdapter
from app.ingestion.world_bank import WorldBankAdapter


SAMPLE_COUNTRIES = ["DEU", "USA", "IND"]


def main() -> int:
    world_bank = WorldBankAdapter(timeout_seconds=90, max_retries=2)
    imf = IMFAdapter(timeout_seconds=90, max_retries=2)
    un_wpp = UNWPPAdapter(timeout_seconds=180, max_retries=2)

    try:
        catalog = world_bank.fetch_country_catalog()
        catalog_by_iso3 = {
            country["iso3"]: country
            for country in catalog
        }

        wb_metadata, wb_observations = world_bank.fetch_indicator_many(
            SAMPLE_COUNTRIES,
            "SP.POP.TOTL",
            start_year=2023,
            end_year=2025,
        )
        wb_rows = world_bank.normalize_many(
            SAMPLE_COUNTRIES,
            {
                "indicator_id": "population_total",
                "source_indicator": "SP.POP.TOTL",
                "unit": "persons",
            },
            wb_metadata,
            wb_observations,
        )

        imf_config = IMF_SERIES[0]
        imf_payload = imf.fetch_indicator(imf_config["source_indicator"])
        imf_coverage = {}
        for code in SAMPLE_COUNTRIES:
            try:
                rows = imf.normalize(code, imf_config, imf_payload)
            except ValueError:
                rows = []
            imf_coverage[code] = len(rows)

        wpp_csv = un_wpp.fetch_csv()
        wpp_rows = un_wpp.normalize_countries(
            SAMPLE_COUNTRIES,
            wpp_csv,
        )
    finally:
        world_bank.close()
        imf.close()
        un_wpp.close()

    wb_coverage = {
        code: sum(
            row["country_iso3"] == code
            for row in wb_rows
        )
        for code in SAMPLE_COUNTRIES
    }
    wpp_coverage = {
        code: sum(
            row["country_iso3"] == code
            for row in wpp_rows
        )
        for code in SAMPLE_COUNTRIES
    }

    payload = {
        "sample_countries": SAMPLE_COUNTRIES,
        "catalog_country_count": len(catalog),
        "catalog_metadata": {
            code: {
                "name": catalog_by_iso3.get(code, {}).get("name"),
                "iso2": catalog_by_iso3.get(code, {}).get("iso2"),
                **country_membership_flags(code),
            }
            for code in SAMPLE_COUNTRIES
        },
        "world_bank_population_rows": wb_coverage,
        "imf_real_gdp_growth_rows": imf_coverage,
        "un_wpp_rows": wpp_coverage,
    }
    print(json.dumps(payload, indent=2, default=str))

    if len(catalog) < 100:
        return 2
    if any(code not in catalog_by_iso3 for code in SAMPLE_COUNTRIES):
        return 3
    if any(count == 0 for count in wb_coverage.values()):
        return 4
    if any(count == 0 for count in wpp_coverage.values()):
        return 5
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
