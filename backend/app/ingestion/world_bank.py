from datetime import datetime, timezone

import httpx

from app.catalog import INDICATORS
from app.db.analytics import upsert_observations

BASE_URL = "https://api.worldbank.org/v2"
SOURCE_ID = "WORLD_BANK"
DATASET_ID = "WDI"


class WorldBankAdapter:
    def __init__(self, client: httpx.Client | None = None):
        self.client = client or httpx.Client(timeout=30.0, follow_redirects=True)
        self._owns_client = client is None

    def close(self) -> None:
        if self._owns_client:
            self.client.close()

    def fetch_indicator(
        self,
        country_iso3: str,
        source_indicator: str,
        start_year: int = 2000,
        end_year: int = 2026,
    ) -> tuple[dict, list[dict]]:
        response = self.client.get(
            f"{BASE_URL}/country/{country_iso3}/indicator/{source_indicator}",
            params={
                "format": "json",
                "date": f"{start_year}:{end_year}",
                "per_page": 100,
            },
        )
        response.raise_for_status()
        payload = response.json()

        if not isinstance(payload, list) or len(payload) < 2:
            raise ValueError(f"Unexpected World Bank response for {source_indicator}")

        metadata = payload[0] or {}
        observations = payload[1] or []
        return metadata, observations

    def normalize(
        self,
        country_iso3: str,
        indicator: dict,
        metadata: dict,
        observations: list[dict],
    ) -> list[dict]:
        retrieved_at = datetime.now(timezone.utc)
        rows: list[dict] = []

        for observation in observations:
            value = observation.get("value")
            date = observation.get("date")
            if value is None or not date or not str(date).isdigit():
                continue

            rows.append(
                {
                    "country_iso3": country_iso3.upper(),
                    "indicator_id": indicator["indicator_id"],
                    "period": int(date),
                    "value": float(value),
                    "unit": indicator["unit"],
                    "source_id": SOURCE_ID,
                    "dataset_id": DATASET_ID,
                    "observation_type": (
                        "official_forecast"
                        if observation.get("obs_status") == "F"
                        else "observed"
                    ),
                    "retrieved_at": retrieved_at,
                    "source_updated_at": metadata.get("lastupdated"),
                    "source_observation_status": observation.get("obs_status"),
                    "source_decimal": observation.get("decimal"),
                }
            )

        return rows

    def sync_country(
        self,
        country_iso3: str,
        start_year: int = 2000,
        end_year: int = 2026,
    ) -> dict:
        total_rows = 0
        details = []

        for indicator in INDICATORS:
            metadata, observations = self.fetch_indicator(
                country_iso3,
                indicator["source_indicator"],
                start_year,
                end_year,
            )
            rows = self.normalize(
                country_iso3,
                indicator,
                metadata,
                observations,
            )
            inserted = upsert_observations(rows)
            total_rows += inserted
            details.append(
                {
                    "indicator_id": indicator["indicator_id"],
                    "source_indicator": indicator["source_indicator"],
                    "rows": inserted,
                    "source_updated_at": metadata.get("lastupdated"),
                }
            )

        return {
            "country_iso3": country_iso3.upper(),
            "source": SOURCE_ID,
            "rows": total_rows,
            "indicators": details,
        }
