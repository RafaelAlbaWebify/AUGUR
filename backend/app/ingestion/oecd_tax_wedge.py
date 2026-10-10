"""Fetch and strictly normalize OECD annual average tax wedge CSV.

Only a single-person, childless, 100%-average-wage observation is accepted.
"""
from __future__ import annotations

import csv
import io
import math
from datetime import datetime, timezone

import httpx

from app.services.tax_wedge_contract import TAX_WEDGE_CONTRACT

COUNTRIES = {"ESP", "IRL", "PRT"}
REQUIRED = {"REF_AREA", "MEASURE", "HH_TYPE", "EARN_PRINCIPAL", "EARN_SPOUSE", "FREQ", "TIME_PERIOD", "OBS_VALUE"}


def fetch_tax_wedge_csv(client: httpx.Client, start_year: int = 2010) -> str:
    """Fetch narrowly scoped country records; do not mask upstream failures."""
    chunks = []
    for country in ("ESP", "IRL", "PRT"):
        url = TAX_WEDGE_CONTRACT["api_url"].replace(
            "/.AV_TW..S_C0.AW100._Z.A",
            f"/{country}.AV_TW..S_C0.AW100._Z.A",
        )
        response = client.get(
            url,
            params={"startPeriod": str(start_year), "format": "csvfile",
                    "dimensionAtObservation": "AllDimensions"},
            timeout=90.0,
        )
        response.raise_for_status()
        text = response.text
        lines = text.splitlines()
        if len(lines) < 2:
            raise ValueError(f"Empty OECD source response for {country}")
        if not chunks:
            chunks.append(lines[0])
        elif lines[0] != chunks[0]:
            raise ValueError(f"Inconsistent OECD country CSV columns for {country}")
        chunks.extend(lines[1:])
    return "\\n".join(chunks) + "\\n"


def normalize_tax_wedge(csv_text: str) -> list[dict]:
    reader = csv.DictReader(io.StringIO(csv_text))
    missing = REQUIRED - set(reader.fieldnames or ())
    if missing:
        raise ValueError("OECD tax-wedge CSV missing columns: " + ", ".join(sorted(missing)))
    now = datetime.now(timezone.utc)
    results = []
    seen = set()
    for row in reader:
        country = row["REF_AREA"]
        if country not in COUNTRIES:
            continue
        if (row["MEASURE"] != "AV_TW" or row["HH_TYPE"] != "S_C0"
                or row["EARN_PRINCIPAL"] != "AW100" or row["EARN_SPOUSE"] != "_Z"
                or row["FREQ"] != "A"):
            raise ValueError("Unexpected OECD tax-wedge series dimensions for " + country)
        if not row["TIME_PERIOD"].isdigit() or not row["OBS_VALUE"]:
            continue
        value = float(row["OBS_VALUE"])
        if not math.isfinite(value) or not (-100 <= value <= 100):
            raise ValueError("Invalid tax wedge observation")
        key = (country, int(row["TIME_PERIOD"]))
        if key in seen:
            raise ValueError("Duplicate OECD tax wedge observation " + str(key))
        seen.add(key)
        results.append({
            "country_iso3": country, "indicator_id": "oecd_tax_wedge_average_wage",
            "period": key[1], "value": value, "unit": "percent_of_total_labour_cost",
            "source_id": "OECD", "dataset_id": TAX_WEDGE_CONTRACT["dataflow"],
            "observation_type": "observed", "retrieved_at": now,
            "source_updated_at": None,
            "source_observation_status": row.get("OBS_STATUS"),
            "source_decimal": None,
        })
    return results
