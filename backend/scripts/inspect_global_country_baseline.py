from __future__ import annotations

import argparse
import json

from app.catalog import country_membership_flags
from app.ingestion.imf import IMFAdapter, SERIES as IMF_SERIES
from app.ingestion.un_wpp import UNWPPAdapter
from app.ingestion.world_bank import WorldBankAdapter


SAMPLE_COUNTRIES = ["DEU", "USA", "IND"]


def probe_world_bank() -> dict:
    adapter = WorldBankAdapter(timeout_seconds=90, max_retries=2)
    try:
        catalog = adapter.fetch_country_catalog()
        catalog_by_iso3 = {
            country["iso3"]: country
            for country in catalog
        }
        metadata, observations = adapter.fetch_indicator_many(
            SAMPLE_COUNTRIES,
            "SP.POP.TOTL",
            start_year=2023,
            end_year=2025,
        )
        rows = adapter.normalize_many(
            SAMPLE_COUNTRIES,
            {
                "indicator_id": "population_total",
                "source_indicator": "SP.POP.TOTL",
                "unit": "persons",
            },
            metadata,
            observations,
        )
    finally:
        adapter.close()

    coverage = {
        code: sum(row["country_iso3"] == code for row in rows)
        for code in SAMPLE_COUNTRIES
    }
    return {
        "source": "WORLD_BANK",
        "catalog_country_count": len(catalog),
        "catalog_metadata": {
            code: {
                "name": catalog_by_iso3.get(code, {}).get("name"),
                "iso2": catalog_by_iso3.get(code, {}).get("iso2"),
                **country_membership_flags(code),
            }
            for code in SAMPLE_COUNTRIES
        },
        "population_rows": coverage,
        "ok": (
            len(catalog) >= 100
            and all(code in catalog_by_iso3 for code in SAMPLE_COUNTRIES)
            and all(count > 0 for count in coverage.values())
        ),
    }


def probe_imf() -> dict:
    import httpx

    adapter = IMFAdapter(timeout_seconds=90, max_retries=2)
    try:
        config = IMF_SERIES[0]
        try:
            payload = adapter.fetch_indicator(config["source_indicator"])
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 403:
                return {
                    "source": "IMF",
                    "indicator": config["source_indicator"],
                    "status": "source_access_restricted_in_ci",
                    "http_status": 403,
                    "ok": True,
                    "full_sample_coverage": False,
                    "notes": [
                        "IMF DataMapper v2 and v1 reject the GitHub-hosted runner with HTTP 403.",
                        "This is treated as CI transport restriction, not missing country evidence.",
                    ],
                }
            raise

        coverage = {}
        for code in SAMPLE_COUNTRIES:
            try:
                rows = adapter.normalize(code, config, payload)
            except ValueError:
                rows = []
            coverage[code] = len(rows)
    finally:
        adapter.close()

    values = payload.get("values") if isinstance(payload, dict) else None
    return {
        "source": "IMF",
        "indicator": config["source_indicator"],
        "status": "available",
        "payload_top_level_keys": sorted(payload) if isinstance(payload, dict) else [],
        "value_keys": sorted(values)[:20] if isinstance(values, dict) else [],
        "rows": coverage,
        "ok": any(count > 0 for count in coverage.values()),
        "full_sample_coverage": all(
            count > 0 for count in coverage.values()
        ),
    }


def probe_un_wpp() -> dict:
    adapter = UNWPPAdapter(timeout_seconds=180, max_retries=2)
    try:
        csv_text = adapter.fetch_csv()
        rows = adapter.normalize_countries(
            SAMPLE_COUNTRIES,
            csv_text,
        )
    finally:
        adapter.close()

    coverage = {
        code: sum(row["country_iso3"] == code for row in rows)
        for code in SAMPLE_COUNTRIES
    }
    return {
        "source": "UN_WPP",
        "rows": coverage,
        "ok": all(count > 0 for count in coverage.values()),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Probe AUGUR global baseline sources with representative countries."
    )
    parser.add_argument(
        "--source",
        choices=["world_bank", "imf", "un_wpp", "all"],
        default="all",
    )
    args = parser.parse_args()

    probes = []
    if args.source in {"world_bank", "all"}:
        probes.append(probe_world_bank())
    if args.source in {"imf", "all"}:
        probes.append(probe_imf())
    if args.source in {"un_wpp", "all"}:
        probes.append(probe_un_wpp())

    payload = {
        "sample_countries": SAMPLE_COUNTRIES,
        "probes": probes,
    }
    print(json.dumps(payload, indent=2, default=str))
    return 0 if all(item["ok"] for item in probes) else 2


if __name__ == "__main__":
    raise SystemExit(main())
