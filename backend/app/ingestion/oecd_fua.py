from __future__ import annotations

import csv
import io
import time
from datetime import datetime, timezone

import httpx

from app.db.analytics import upsert_subnational_observations


SOURCE_ID = "OECD"
DATASET_ID = "DSD_FUA_TERR@DF_DENSITY"
DATASET_VERSION = "1.1"
GEOGRAPHY_SYSTEM = "OECD_FUA"
BASE_URL = (
    "https://sdmx.oecd.org/public/rest/data/"
    "OECD.CFE.EDS,DSD_FUA_TERR@DF_DENSITY,1.1"
)
DEFAULT_KEY = ".A.POP_DEN.."
PARAMS = {
    "dimensionAtObservation": "AllDimensions",
    "format": "csvfilewithlabels",
}


def _reference_name(record: dict, code: str) -> str:
    return str(
        record.get("Reference area")
        or record.get("REF_AREA_LABEL")
        or code
    )


def _geo_level(record: dict, code: str) -> str | None:
    published = str(record.get("TERRITORIAL_LEVEL") or "").strip().lower()
    if published in {"city", "fua"}:
        return published
    if code.endswith("C"):
        return "city"
    if code.endswith("F"):
        return "fua"
    return None


def _country_prefix_map(countries: list[dict]) -> list[tuple[str, str]]:
    prefixes: list[tuple[str, str]] = []
    for country in countries:
        iso3 = str(country.get("iso3") or "").upper()
        iso2 = str(country.get("iso2") or "").upper()
        if iso3:
            prefixes.append((iso3, iso3))
        if iso2:
            prefixes.append((iso2, iso3))
    return sorted(set(prefixes), key=lambda item: (-len(item[0]), item[0]))


def _country_for_code(
    code: str,
    prefixes: list[tuple[str, str]],
) -> tuple[str | None, str | None]:
    for prefix, iso3 in prefixes:
        if code.startswith(prefix):
            iso2 = prefix if len(prefix) == 2 else None
            return iso3 or None, iso2
    return None, None


class OECDFUAAdapter:
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
        start_year: int = 2020,
        end_year: int | None = None,
        key: str = DEFAULT_KEY,
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
                    f"{BASE_URL}/{key}",
                    params=params,
                )
                response.raise_for_status()
                text = response.text
                if (
                    "REF_AREA" not in text
                    or "OBS_VALUE" not in text
                    or "TERRITORIAL_LEVEL" not in text
                ):
                    raise ValueError("Unexpected OECD FUA density CSV schema")
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
        raise RuntimeError("OECD FUA density request failed without an exception")

    def normalize_density(
        self,
        csv_text: str,
        *,
        countries: list[dict],
        allowed_country_iso3: set[str] | None = None,
    ) -> list[dict]:
        allowed = (
            {code.upper() for code in allowed_country_iso3}
            if allowed_country_iso3 is not None
            else None
        )
        prefixes = _country_prefix_map(countries)
        retrieved_at = datetime.now(timezone.utc)
        reader = csv.DictReader(io.StringIO(csv_text))
        rows: list[dict] = []

        for record in reader:
            if str(record.get("MEASURE") or "").upper() != "POP_DEN":
                continue
            if str(record.get("UNIT_MEASURE") or "").upper() != "PS_KM2":
                continue

            code = str(record.get("REF_AREA") or "").upper()
            if not code:
                continue

            level = _geo_level(record, code)
            if level not in {"city", "fua"}:
                continue

            country_iso3, inferred_iso2 = _country_for_code(code, prefixes)
            if not country_iso3:
                continue
            if allowed is not None and country_iso3 not in allowed:
                continue

            country = next(
                (
                    item
                    for item in countries
                    if str(item.get("iso3") or "").upper() == country_iso3
                ),
                {},
            )
            country_iso2 = (
                str(country.get("iso2") or "").upper()
                or inferred_iso2
                or None
            )

            period = str(record.get("TIME_PERIOD") or "")
            raw_value = record.get("OBS_VALUE")
            if not period.isdigit() or raw_value in (None, "", ".."):
                continue

            try:
                value = float(raw_value)
            except (TypeError, ValueError):
                continue

            rows.append({
                "geo_code": code,
                "geo_name": _reference_name(record, code),
                "geo_level": level,
                "indicator_id": "urban_population_density",
                "period": int(period),
                "value": value,
                "unit": "people_per_km2",
                "source_id": SOURCE_ID,
                "dataset_id": DATASET_ID,
                "retrieved_at": retrieved_at,
                "source_updated_at": DATASET_VERSION,
                "country_iso3": country_iso3,
                "country_iso2": country_iso2,
                "geography_system": GEOGRAPHY_SYSTEM,
                "source_geo_code": code,
            })

        return rows

    def sync_density(
        self,
        *,
        countries: list[dict],
        allowed_country_iso3: set[str] | None = None,
        start_year: int = 2020,
        end_year: int | None = None,
        key: str = DEFAULT_KEY,
    ) -> dict:
        csv_text = self.fetch_density(
            start_year=start_year,
            end_year=end_year,
            key=key,
        )
        rows = self.normalize_density(
            csv_text,
            countries=countries,
            allowed_country_iso3=allowed_country_iso3,
        )
        inserted = upsert_subnational_observations(rows)

        return {
            "source_id": SOURCE_ID,
            "dataset_id": DATASET_ID,
            "dataset_version": DATASET_VERSION,
            "geography_system": GEOGRAPHY_SYSTEM,
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
            "city_count": len({
                row["geo_code"]
                for row in rows
                if row["geo_level"] == "city"
            }),
            "fua_count": len({
                row["geo_code"]
                for row in rows
                if row["geo_level"] == "fua"
            }),
            "period_min": min((row["period"] for row in rows), default=None),
            "period_max": max((row["period"] for row in rows), default=None),
            "complete": bool(rows),
        }
