"""Synchronize verified OECD annual tax wedge observations into local AUGUR DuckDB."""
from __future__ import annotations

import argparse
import json

import httpx

from app.db.analytics import upsert_observations
from app.db.bootstrap import initialize_datastores
from app.ingestion.oecd_tax_wedge import fetch_tax_wedge_csv, normalize_tax_wedge


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start-year", type=int, default=2010)
    args = parser.parse_args()
    with httpx.Client(follow_redirects=True, headers={"User-Agent": "AUGUR/0.1"}) as client:
        rows = normalize_tax_wedge(fetch_tax_wedge_csv(client, args.start_year))
    coverage = {c: sorted(r["period"] for r in rows if r["country_iso3"] == c)
                for c in ("ESP", "IRL", "PRT")}
    if any(not v for v in coverage.values()):
        raise SystemExit("OECD tax wedge incomplete for requested countries; nothing written")
    initialize_datastores()
    stored = upsert_observations(rows)
    print(json.dumps({
        "dataset": "OECD Taxing Wages (single worker, no children, 100% national average wage)",
        "stored_observations": stored, "country_periods": coverage,
        "warning": "Tax wedge is percent of labour cost; not personal tax or net earnings.",
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
