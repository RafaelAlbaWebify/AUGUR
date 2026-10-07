from __future__ import annotations

import csv
import io
import time
from datetime import datetime, timezone

import httpx

from app.db.analytics import upsert_subnational_observations


SOURCE_ID = "OECD"
DATASET_ID = "DSD_REG_DEMO@DF_DENSITY"
DATASET_VERSION = "2.4"
GEOGRAPHY_SYSTEM = "OECD_TL_2024"
DENSITY_BASE_URL = (
    "https://sdmx.oecd.org/public/rest/data/"
    "OECD.CFE.EDS,DSD_REG_DEMO@DF_DENSITY,2.4"
)
POPULATION_DATASET_ID = "DSD_REG_DEMO@DF_POP_BROAD"
POPULATION_BASE_URL = (
    "https://sdmx.oecd.org/public/rest/data/"
    "OECD.CFE.EDS,DSD_REG_DEMO@DF_POP_BROAD,2.4"
)

PARAMS = {
    "dimensionAtObservation": "AllDimensions",
    "format": "csvfilewithlabels",
}


def _first_present(record: dict, candidates: tuple[str, ...]) -> str | None:
    for key in candidates:
        value = record.get(key)
        if value not in (None, ""):
            return str(value)
    return None


def _reference_name(record: dict, code: str) -> str:
    candidates = (
        "Reference area",
        "REF_AREA_LABEL",
        "REF_AREA_NAME",
        "Reference Area",
    )
    return _first_present(record, candidates) or code


class OECDRegionalAdapter:
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

    def fetch_density(
        self,
        *,
        start_year: int = 2021,
        end_year: int | None = None,
        key: str = "all",
    ) -> str:
        params = {
            **PARAMS,
            "startPeriod": str(start_year),
        }
        if end_year is not None:
            params["endPeriod"] = str(end_year)

        last_error: Exception | None = None

        for attempt in range(1, self.max_retries + 1):
            try:
                response = self.client.get(
                    f"{DENSITY_BASE_URL}/{key}",
                    params=params,
                )
                response.raise_for_status()

                text = response.text
                if "REF_AREA" not in text or "OBS_VALUE" not in text:
                    raise ValueError("Unexpected OECD regional density CSV schema")

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

        raise RuntimeError("OECD regional density request failed without an exception")

    def fetch_population(
        self,
        *,
        start_year: int = 2021,
        end_year: int | None = None,
        key: str = "all",
    ) -> str:
        params = {
            **PARAMS,
            "startPeriod": str(start_year),
        }
        if end_year is not None:
            params["endPeriod"] = str(end_year)

        last_error: Exception | None = None
        for attempt in range(1, self.max_retries + 1):
            try:
                response = self.client.get(
                    f"{POPULATION_BASE_URL}/{key}",
                    params=params,
                )
                response.raise_for_status()
                text = response.text
                if (
                    "REF_AREA" not in text
                    or "OBS_VALUE" not in text
                    or "MEASURE" not in text
                ):
                    raise ValueError(
                        "Unexpected OECD regional population CSV schema"
                    )
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
        raise RuntimeError(
            "OECD regional population request failed without an exception"
        )

    def normalize_density(
        self,
        csv_text: str,
        *,
        allowed_country_iso3: set[str] | None = None,
    ) -> list[dict]:
        reader = csv.DictReader(io.StringIO(csv_text))
        retrieved_at = datetime.now(timezone.utc)
        allowed = (
            {code.upper() for code in allowed_country_iso3}
            if allowed_country_iso3 is not None
            else None
        )
        rows: list[dict] = []

        for record in reader:
            level = str(record.get("TERRITORIAL_LEVEL") or "").upper()
            if level not in {"TL2", "TL3"}:
                continue

            unit = str(record.get("UNIT_MEASURE") or "").upper()
            if unit != "PS_KM2":
                continue

            geo_code = str(record.get("REF_AREA") or "").upper()
            if not geo_code:
                continue

            country_iso3 = str(record.get("COUNTRY") or "").upper() or None
            if allowed is not None and country_iso3 not in allowed:
                continue

            period = str(record.get("TIME_PERIOD") or "")
            raw_value = record.get("OBS_VALUE")
            if not period.isdigit() or raw_value in (None, ""):
                continue

            try:
                value = float(raw_value)
            except (TypeError, ValueError):
                continue

            rows.append(
                {
                    "geo_code": geo_code,
                    "geo_name": _reference_name(record, geo_code),
                    "geo_level": level.lower(),
                    "indicator_id": "regional_population_density",
                    "period": int(period),
                    "value": value,
                    "unit": "people_per_km2",
                    "source_id": SOURCE_ID,
                    "dataset_id": DATASET_ID,
                    "retrieved_at": retrieved_at,
                    "source_updated_at": DATASET_VERSION,
                    "country_iso3": country_iso3,
                    "country_iso2": geo_code[:2] if len(geo_code) >= 2 else None,
                    "geography_system": GEOGRAPHY_SYSTEM,
                    "source_geo_code": geo_code,
                }
            )

        return rows

    def normalize_population(
        self,
        csv_text: str,
        *,
        allowed_country_iso3: set[str] | None = None,
    ) -> list[dict]:
        reader = csv.DictReader(io.StringIO(csv_text))
        retrieved_at = datetime.now(timezone.utc)
        allowed = (
            {code.upper() for code in allowed_country_iso3}
            if allowed_country_iso3 is not None
            else None
        )
        rows: list[dict] = []

        for record in reader:
            level = str(record.get("TERRITORIAL_LEVEL") or "").upper()
            if level not in {"TL2", "TL3"}:
                continue
            if str(record.get("MEASURE") or "").upper() != "POP":
                continue
            if str(record.get("AGE") or "").upper() not in {"_T", "TOTAL"}:
                continue
            if str(record.get("SEX") or "").upper() not in {"_T", "T", "TOTAL"}:
                continue

            geo_code = str(record.get("REF_AREA") or "").upper()
            country_iso3 = str(record.get("COUNTRY") or "").upper() or None
            if not geo_code:
                continue
            if allowed is not None and country_iso3 not in allowed:
                continue

            period = str(record.get("TIME_PERIOD") or "")
            raw_value = record.get("OBS_VALUE")
            if not period.isdigit() or raw_value in (None, ""):
                continue

            try:
                value = float(raw_value)
            except (TypeError, ValueError):
                continue

            rows.append(
                {
                    "geo_code": geo_code,
                    "geo_name": _reference_name(record, geo_code),
                    "geo_level": level.lower(),
                    "indicator_id": "regional_population",
                    "period": int(period),
                    "value": value,
                    "unit": "persons",
                    "source_id": SOURCE_ID,
                    "dataset_id": POPULATION_DATASET_ID,
                    "retrieved_at": retrieved_at,
                    "source_updated_at": DATASET_VERSION,
                    "country_iso3": country_iso3,
                    "country_iso2": geo_code[:2] if len(geo_code) >= 2 else None,
                    "geography_system": GEOGRAPHY_SYSTEM,
                    "source_geo_code": geo_code,
                }
            )

        return rows

    def sync_population(
        self,
        *,
        allowed_country_iso3: set[str] | None = None,
        start_year: int = 2021,
        end_year: int | None = None,
        key: str = "all",
    ) -> dict:
        csv_text = self.fetch_population(
            start_year=start_year,
            end_year=end_year,
            key=key,
        )
        rows = self.normalize_population(
            csv_text,
            allowed_country_iso3=allowed_country_iso3,
        )
        inserted = upsert_subnational_observations(rows)
        return {
            "source_id": SOURCE_ID,
            "dataset_id": POPULATION_DATASET_ID,
            "dataset_version": DATASET_VERSION,
            "rows": inserted,
            "country_count": len({
                row["country_iso3"]
                for row in rows
                if row.get("country_iso3")
            }),
            "geography_count": len({
                row["geo_code"]
                for row in rows
            }),
            "geo_levels": sorted({
                row["geo_level"]
                for row in rows
            }),
            "period_min": min(
                (row["period"] for row in rows),
                default=None,
            ),
            "period_max": max(
                (row["period"] for row in rows),
                default=None,
            ),
            "complete": bool(rows),
        }

    def sync_density(
        self,
        *,
        allowed_country_iso3: set[str] | None = None,
        start_year: int = 2021,
        end_year: int | None = None,
        key: str = "all",
    ) -> dict:
        csv_text = self.fetch_density(
            start_year=start_year,
            end_year=end_year,
            key=key,
        )
        rows = self.normalize_density(
            csv_text,
            allowed_country_iso3=allowed_country_iso3,
        )
        inserted = upsert_subnational_observations(rows)

        countries = sorted({
            row["country_iso3"]
            for row in rows
            if row.get("country_iso3")
        })
        levels = sorted({row["geo_level"] for row in rows})
        geographies = sorted({row["geo_code"] for row in rows})
        periods = sorted({row["period"] for row in rows})

        return {
            "source_id": SOURCE_ID,
            "dataset_id": DATASET_ID,
            "dataset_version": DATASET_VERSION,
            "rows": inserted,
            "country_count": len(countries),
            "countries": countries,
            "geography_count": len(geographies),
            "geo_levels": levels,
            "period_min": min(periods) if periods else None,
            "period_max": max(periods) if periods else None,
            "complete": bool(rows),
        }
