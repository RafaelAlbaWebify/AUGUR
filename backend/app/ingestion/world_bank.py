import time
from datetime import datetime, timezone

import httpx

from app.catalog import country_membership_flags, world_bank_indicators
from app.db.analytics import upsert_country, upsert_observations

BASE_URL = "https://api.worldbank.org/v2"
SOURCE_ID = "WORLD_BANK"
DATASET_ID = "WDI"


class WorldBankAdapter:
    def __init__(
        self,
        client: httpx.Client | None = None,
        timeout_seconds: float = 90.0,
        max_retries: int = 3,
    ):
        self.timeout_seconds = timeout_seconds
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

    def fetch_country_catalog(self) -> list[dict]:
        response = self.client.get(
            f"{BASE_URL}/country",
            params={
                "format": "json",
                "per_page": 400,
            },
        )
        response.raise_for_status()
        payload = response.json()

        if (
            not isinstance(payload, list)
            or len(payload) < 2
            or not isinstance(payload[1], list)
        ):
            raise ValueError("Unexpected World Bank country catalog response")

        countries = []
        for item in payload[1]:
            if not isinstance(item, dict):
                continue

            iso3 = str(item.get("id") or "").upper()
            iso2 = str(item.get("iso2Code") or "").upper()
            name = str(item.get("name") or "").strip()
            region = (
                (item.get("region") or {}).get("value")
                if isinstance(item.get("region"), dict)
                else None
            )
            admin_region = (
                (item.get("adminregion") or {}).get("value")
                if isinstance(item.get("adminregion"), dict)
                else None
            )

            if (
                len(iso3) != 3
                or not iso3.isalpha()
                or len(iso2) != 2
                or not iso2.isalpha()
                or not name
                or region == "Aggregates"
            ):
                continue

            countries.append({
                "iso2": iso2,
                "iso3": iso3,
                "name": name,
                "region": region,
                "subregion": admin_region or None,
                "currency": None,
                "capital_city": (str(item.get("capitalCity") or "").strip() or None),
                "latitude": (
                    float(item["latitude"])
                    if item.get("latitude") not in (None, "")
                    else None
                ),
                "longitude": (
                    float(item["longitude"])
                    if item.get("longitude") not in (None, "")
                    else None
                ),
                **country_membership_flags(iso3),
            })

        if not countries:
            raise ValueError("World Bank country catalog contained no countries")

        return countries

    def register_country_catalog(self) -> list[dict]:
        countries = self.fetch_country_catalog()
        for country in countries:
            upsert_country(country)
        return countries

    def fetch_country_metadata(self, country_iso3: str) -> dict:
        code = country_iso3.upper()
        response = self.client.get(
            f"{BASE_URL}/country/{code}",
            params={"format": "json"},
        )
        response.raise_for_status()
        payload = response.json()

        if (
            not isinstance(payload, list)
            or len(payload) < 2
            or not isinstance(payload[1], list)
            or not payload[1]
        ):
            raise ValueError(f"World Bank has no country metadata for {code}")

        item = payload[1][0]
        if not isinstance(item, dict):
            raise ValueError(f"Unexpected World Bank country metadata for {code}")

        iso3 = str(item.get("id") or code).upper()
        iso2 = str(item.get("iso2Code") or "").upper() or None
        name = str(item.get("name") or iso3).strip()
        region = (
            (item.get("region") or {}).get("value")
            if isinstance(item.get("region"), dict)
            else None
        )
        if region == "Aggregates":
            raise ValueError(f"{code} is a World Bank aggregate, not a country")

        admin_region = (
            (item.get("adminregion") or {}).get("value")
            if isinstance(item.get("adminregion"), dict)
            else None
        )

        if not iso3 or not name:
            raise ValueError(f"Incomplete World Bank country metadata for {code}")

        return {
            "iso2": iso2,
            "iso3": iso3,
            "name": name,
            "region": region,
            "subregion": admin_region or None,
            "currency": None,
            "capital_city": (str(item.get("capitalCity") or "").strip() or None),
            "latitude": (
                float(item["latitude"])
                if item.get("latitude") not in (None, "")
                else None
            ),
            "longitude": (
                float(item["longitude"])
                if item.get("longitude") not in (None, "")
                else None
            ),
            **country_membership_flags(iso3),
        }

    def ensure_country_registered(self, country_iso3: str) -> dict:
        metadata = self.fetch_country_metadata(country_iso3)
        upsert_country(metadata)
        return metadata

    def fetch_indicator(
        self,
        country_iso3: str,
        source_indicator: str,
        start_year: int = 2000,
        end_year: int = 2026,
    ) -> tuple[dict, list[dict]]:
        url = f"{BASE_URL}/country/{country_iso3}/indicator/{source_indicator}"
        params = {
            "format": "json",
            "date": f"{start_year}:{end_year}",
            "per_page": 100,
        }

        last_error: Exception | None = None

        for attempt in range(1, self.max_retries + 1):
            try:
                response = self.client.get(url, params=params)
                response.raise_for_status()
                payload = response.json()

                if not isinstance(payload, list) or len(payload) < 2:
                    raise ValueError(
                        f"Unexpected World Bank response for {source_indicator}"
                    )

                metadata = payload[0] or {}
                observations = payload[1] or []
                return metadata, observations

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

        assert last_error is not None
        raise last_error

    def fetch_indicator_many(
        self,
        country_iso3s: list[str],
        source_indicator: str,
        start_year: int = 2000,
        end_year: int = 2026,
    ) -> tuple[dict, list[dict]]:
        countries = sorted({
            code.upper()
            for code in country_iso3s
            if code
        })
        if not countries:
            return {}, []

        url = (
            f"{BASE_URL}/country/{';'.join(countries)}"
            f"/indicator/{source_indicator}"
        )
        params = {
            "format": "json",
            "date": f"{start_year}:{end_year}",
            "per_page": 20000,
        }

        last_error: Exception | None = None
        for attempt in range(1, self.max_retries + 1):
            try:
                response = self.client.get(url, params=params)
                response.raise_for_status()
                payload = response.json()

                if not isinstance(payload, list) or len(payload) < 2:
                    raise ValueError(
                        f"Unexpected World Bank batch response for {source_indicator}"
                    )

                metadata = payload[0] or {}
                observations = payload[1] or []
                pages = int(metadata.get("pages") or 1)

                for page in range(2, pages + 1):
                    page_response = self.client.get(
                        url,
                        params={**params, "page": page},
                    )
                    page_response.raise_for_status()
                    page_payload = page_response.json()
                    if (
                        isinstance(page_payload, list)
                        and len(page_payload) >= 2
                        and isinstance(page_payload[1], list)
                    ):
                        observations.extend(page_payload[1])

                return metadata, observations

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
        raise RuntimeError("World Bank batch request failed without an exception")

    def normalize_many(
        self,
        country_iso3s: list[str],
        indicator: dict,
        metadata: dict,
        observations: list[dict],
    ) -> list[dict]:
        targets = {
            code.upper()
            for code in country_iso3s
        }
        grouped: dict[str, list[dict]] = {
            code: []
            for code in targets
        }

        for observation in observations:
            code = str(
                observation.get("countryiso3code")
                or observation.get("country", {}).get("id")
                or ""
            ).upper()
            if code in grouped:
                grouped[code].append(observation)

        rows: list[dict] = []
        for code, country_observations in grouped.items():
            rows.extend(
                self.normalize(
                    code,
                    indicator,
                    metadata,
                    country_observations,
                )
            )
        return rows

    def sync_countries(
        self,
        country_iso3s: list[str],
        start_year: int = 2000,
        end_year: int = 2026,
    ) -> dict:
        countries = sorted({
            code.upper()
            for code in country_iso3s
            if code
        })
        indicators = world_bank_indicators()
        total_rows = 0
        details = []
        failures = []

        for index, indicator in enumerate(indicators, start=1):
            print(
                f"[{index}/{len(indicators)}] "
                f"{indicator['indicator_id']} "
                f"({indicator['source_indicator']}) · "
                f"{len(countries)} countries"
            )
            try:
                metadata, observations = self.fetch_indicator_many(
                    countries,
                    indicator["source_indicator"],
                    start_year,
                    end_year,
                )
                rows = self.normalize_many(
                    countries,
                    indicator,
                    metadata,
                    observations,
                )
                inserted = upsert_observations(rows)
                total_rows += inserted
                covered = len({
                    row["country_iso3"]
                    for row in rows
                })
                details.append({
                    "indicator_id": indicator["indicator_id"],
                    "source_indicator": indicator["source_indicator"],
                    "rows": inserted,
                    "countries_with_data": covered,
                    "source_updated_at": metadata.get("lastupdated"),
                })
                print(
                    f"   ok: {inserted} rows · "
                    f"{covered}/{len(countries)} countries"
                )
            except Exception as exc:
                failures.append({
                    "indicator_id": indicator["indicator_id"],
                    "source_indicator": indicator["source_indicator"],
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                })
                print(f"   failed: {type(exc).__name__}: {exc}")

        return {
            "countries": countries,
            "country_count": len(countries),
            "source": SOURCE_ID,
            "rows": total_rows,
            "indicators": details,
            "failures": failures,
            "complete": len(failures) == 0,
        }

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
        failures = []

        indicators = world_bank_indicators()

        for index, indicator in enumerate(indicators, start=1):
            print(
                f"[{index}/{len(indicators)}] "
                f"{indicator['indicator_id']} "
                f"({indicator['source_indicator']})"
            )

            try:
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
                print(f"   ok: {inserted} rows")

            except Exception as exc:
                failures.append(
                    {
                        "indicator_id": indicator["indicator_id"],
                        "source_indicator": indicator["source_indicator"],
                        "error_type": type(exc).__name__,
                        "error": str(exc),
                    }
                )
                print(
                    f"   failed: {type(exc).__name__}: {exc}"
                )

        return {
            "country_iso3": country_iso3.upper(),
            "source": SOURCE_ID,
            "rows": total_rows,
            "indicators": details,
            "failures": failures,
            "complete": len(failures) == 0,
        }
