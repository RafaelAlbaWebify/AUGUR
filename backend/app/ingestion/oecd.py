from __future__ import annotations

import csv
import io
import time
from datetime import datetime, timezone

import httpx

from app.db.analytics import upsert_observations

SOURCE_ID = "OECD"
DATASET_ID = "DSD_PDB@DF_PDB"
BASE_URL = (
    "https://sdmx.oecd.org/public/rest/data/"
    "OECD.SDD.TPS,DSD_PDB@DF_PDB,2.0"
)

PARAMS = {
    "startPeriod": "1995",
    "dimensionAtObservation": "AllDimensions",
    "format": "csvfile",
}


class OECDAdapter:
    def __init__(
        self,
        client: httpx.Client | None = None,
        timeout_seconds: float = 90.0,
        max_retries: int = 3,
    ):
        self.max_retries = max_retries
        self.client = client or httpx.Client(
            timeout=httpx.Timeout(timeout_seconds),
            follow_redirects=True,
            headers={"User-Agent": "AUGUR/0.1"},
        )
        self._owns_client = client is None

    def close(self) -> None:
        if self._owns_client:
            self.client.close()

    def fetch_productivity(self, country_iso3: str) -> str:
        last_error: Exception | None = None

        for attempt in range(1, self.max_retries + 1):
            try:
                url = f"{BASE_URL}/{country_iso3.upper()}.A.GDPHRS._T.USD_PPP_H.LR.N.."
                response = self.client.get(url, params=PARAMS)
                response.raise_for_status()

                if "TIME_PERIOD" not in response.text or "OBS_VALUE" not in response.text:
                    raise ValueError("Unexpected OECD CSV response")

                return response.text

            except (httpx.TimeoutException, httpx.TransportError, httpx.HTTPStatusError) as exc:
                last_error = exc

                if attempt >= self.max_retries:
                    break

                delay_seconds = 2 ** (attempt - 1)
                print(
                    f"   retry {attempt}/{self.max_retries - 1} "
                    f"after {type(exc).__name__} "
                    f"(waiting {delay_seconds}s)"
                )
                time.sleep(delay_seconds)

        if last_error is not None:
            raise last_error

        raise RuntimeError("OECD request failed without an exception")

    def normalize(self, country_iso3: str, csv_text: str) -> list[dict]:
        retrieved_at = datetime.now(timezone.utc)
        reader = csv.DictReader(io.StringIO(csv_text))
        rows: list[dict] = []

        for record in reader:
            period = record.get("TIME_PERIOD")
            value = record.get("OBS_VALUE")

            if not period or not str(period).isdigit():
                continue
            if value in (None, ""):
                continue

            rows.append(
                {
                    "country_iso3": country_iso3.upper(),
                    "indicator_id": "gdp_per_hour_worked",
                    "period": int(period),
                    "value": float(value),
                    "unit": "usd_ppp_per_hour",
                    "source_id": SOURCE_ID,
                    "dataset_id": DATASET_ID,
                    "observation_type": "observed",
                    "retrieved_at": retrieved_at,
                    "source_updated_at": None,
                    "source_observation_status": record.get("OBS_STATUS"),
                    "source_decimal": None,
                }
            )

        if not rows:
            raise ValueError("OECD response contained no usable productivity observations")

        return rows

    def sync_country(self, country_iso3: str) -> dict:
        print(f"[1/1] gdp_per_hour_worked (OECD Productivity database, {country_iso3.upper()})")
        csv_text = self.fetch_productivity(country_iso3)
        rows = self.normalize(country_iso3, csv_text)
        inserted = upsert_observations(rows)
        print(f"   ok: {inserted} rows")

        return {
            "country_iso3": country_iso3.upper(),
            "source": SOURCE_ID,
            "rows": inserted,
            "series": 1,
            "complete": True,
        }
