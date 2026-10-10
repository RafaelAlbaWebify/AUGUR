"""Live-readiness smoke for the official OECD tax wedge series.

Prints metadata and evidence only; never modifies the user's DuckDB.
"""
from __future__ import annotations
import json
import httpx
from app.ingestion.oecd_tax_wedge import fetch_tax_wedge_csv, normalize_tax_wedge


def main():
    with httpx.Client(follow_redirects=True, headers={"User-Agent": "AUGUR/0.1"}) as client:
        raw = fetch_tax_wedge_csv(client, start_year=2024)
    header = raw.splitlines()[0] if raw else ""
    print(json.dumps({'official_csv_columns': header.split(',')}, indent=2), flush=True)
    rows = normalize_tax_wedge(raw)
    result = {
        "scope": "official_oecd_tax_wedge_live_smoke",
        "csv_columns": header.split(","),
        "country_periods": {
            country: sorted(row["period"] for row in rows if row["country_iso3"] == country)
            for country in ("ESP", "IRL", "PRT")
        },
        "observation_count": len(rows),
    }
    print(json.dumps(result, indent=2))
    if not rows or any(not result["country_periods"][c] for c in result["country_periods"]):
        raise SystemExit("Official CSV did not supply a usable series for each requested country")


if __name__ == "__main__":
    main()
