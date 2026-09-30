from __future__ import annotations

import csv
import gzip
import io
import time
from datetime import datetime, timezone

import httpx

from app.db.analytics import upsert_observations

SOURCE_ID = "UN_WPP"
DATASET_ID = "WPP2024_Demographic_Indicators_Medium"
PROJECTION_START_YEAR = 2024

URL = (
    "https://population.un.org/wpp/assets/Excel%20Files/"
    "1_Indicator%20(Standard)/CSV_FILES/"
    "WPP2024_Demographic_Indicators_Medium.csv.gz"
)

FIELD_MAP = {
    "TPopulation1July": {
        "indicator_id": "population_total",
        "unit": "persons",
        "multiplier": 1000.0,
    },
    "TFR": {
        "indicator_id": "fertility_rate",
        "unit": "births_per_woman",
        "multiplier": 1.0,
    },
    "MedianAgePop": {
        "indicator_id": "median_age",
        "unit": "years",
        "multiplier": 1.0,
    },
    "LEx": {
        "indicator_id": "life_expectancy",
        "unit": "years",
        "multiplier": 1.0,
    },
}


class UNWPPAdapter:
    def __init__(
        self,
        client: httpx.Client | None = None,
        timeout_seconds: float = 120.0,
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

    def fetch_csv(self) -> str:
        last_error: Exception | None = None

        for attempt in range(1, self.max_retries + 1):
            try:
                response = self.client.get(URL)
                response.raise_for_status()

                if not response.content:
                    raise ValueError("UN WPP bulk download returned an empty response")

                try:
                    raw = gzip.decompress(response.content)
                except OSError as exc:
                    raise ValueError(
                        "UN WPP bulk response was not valid gzip data"
                    ) from exc

                text = raw.decode("utf-8-sig")

                if "ISO3_code" not in text or "TPopulation1July" not in text:
                    raise ValueError("Unexpected UN WPP CSV schema")

                return text

            except (
                httpx.TimeoutException,
                httpx.TransportError,
                httpx.HTTPStatusError,
            ) as exc:
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

        raise RuntimeError("UN WPP request failed without an exception")

    def normalize(self, csv_text: str) -> list[dict]:
        reader = csv.DictReader(io.StringIO(csv_text))
        retrieved_at = datetime.now(timezone.utc)
        rows: list[dict] = []

        for record in reader:
            if record.get("ISO3_code") != "ESP":
                continue

            variant = (record.get("Variant") or "").strip().lower()
            if variant and variant != "medium":
                continue

            year_text = record.get("Time")
            if not year_text or not str(year_text).isdigit():
                continue

            year = int(year_text)
            observation_type = (
                "official_forecast"
                if year >= PROJECTION_START_YEAR
                else "observed"
            )

            for field_name, config in FIELD_MAP.items():
                raw_value = record.get(field_name)

                if raw_value in (None, "", ".."):
                    continue

                rows.append(
                    {
                        "country_iso3": "ESP",
                        "indicator_id": config["indicator_id"],
                        "period": year,
                        "value": float(raw_value) * config["multiplier"],
                        "unit": config["unit"],
                        "source_id": SOURCE_ID,
                        "dataset_id": DATASET_ID,
                        "observation_type": observation_type,
                        "retrieved_at": retrieved_at,
                        "source_updated_at": "2024",
                        "source_observation_status": (
                            "medium_projection"
                            if observation_type == "official_forecast"
                            else "estimate"
                        ),
                        "source_decimal": None,
                    }
                )

        if not rows:
            raise ValueError("UN WPP CSV contained no usable Spain observations")

        return rows

    def sync_spain(self) -> dict:
        print("[1/1] UN WPP 2024 demographic indicators (Spain)")
        csv_text = self.fetch_csv()
        rows = self.normalize(csv_text)
        inserted = upsert_observations(rows)

        observed = sum(row["observation_type"] == "observed" for row in rows)
        forecasts = sum(
            row["observation_type"] == "official_forecast" for row in rows
        )

        indicators = sorted({row["indicator_id"] for row in rows})

        print(
            f"   ok: {inserted} rows "
            f"({observed} observed, {forecasts} forecasts)"
        )

        return {
            "country_iso3": "ESP",
            "source": SOURCE_ID,
            "vintage": "WPP 2024 medium variant",
            "rows": inserted,
            "observed": observed,
            "official_forecasts": forecasts,
            "indicators": indicators,
            "complete": True,
        }
