from __future__ import annotations

import httpx


SWAGGER_URL = (
    "https://eeadmz1-downloads-api-appservice.azurewebsites.net/"
    "swagger/v1/swagger.json"
)
API_BASE = "https://eeadmz1-downloads-api-appservice.azurewebsites.net"
TARGET_COUNTRIES = ["ES", "PT", "IE"]
PM25_URI = "http://dd.eionet.europa.eu/vocabulary/aq/pollutant/6001"


def _safe_json(response: httpx.Response):
    try:
        return response.json()
    except Exception:
        return {"raw_text": response.text[:4000]}


def inspect_modern_eea_api(
    client: httpx.Client | None = None,
) -> dict:
    owns_client = client is None
    active = client or httpx.Client(
        timeout=120,
        follow_redirects=True,
        headers={"User-Agent": "AUGUR/0.1 EEA Air Quality API inspector"},
    )
    try:
        response = active.get(SWAGGER_URL)
        response.raise_for_status()
        payload = response.json()

        country_response = active.get(f"{API_BASE}/Country")
        pollutant_response = active.get(f"{API_BASE}/Pollutant")
        city_response = active.post(
            f"{API_BASE}/City",
            json=TARGET_COUNTRIES,
        )
        summary_payload = {
            "countries": ["ES"],
            "cities": [],
            "pollutants": [PM25_URI],
            "dataset": 2,
            "source": "API",
            "dateTimeStart": "2024-01-01T00:00:00Z",
            "dateTimeEnd": "2024-12-31T23:59:59Z",
        }
        summary_response = active.post(
            f"{API_BASE}/DownloadSummary",
            json=summary_payload,
        )
    finally:
        if owns_client:
            active.close()

    paths = payload.get("paths") or {}
    interesting = {}
    for path, operations in paths.items():
        text = f"{path} {operations}".lower()
        if any(
            token in text
            for token in (
                "download",
                "air",
                "pollut",
                "country",
                "station",
                "parquet",
                "timeseries",
            )
        ):
            interesting[path] = {
                method: {
                    "summary": operation.get("summary"),
                    "parameters": [
                        {
                            "name": parameter.get("name"),
                            "in": parameter.get("in"),
                            "required": parameter.get("required"),
                            "schema": parameter.get("schema"),
                        }
                        for parameter in operation.get("parameters", [])
                    ],
                    "request_body": operation.get("requestBody"),
                }
                for method, operation in operations.items()
                if method.lower() in {"get", "post"}
            }

    schemas = payload.get("components", {}).get("schemas", {})
    referenced_schema_names = set()
    for operations in interesting.values():
        for operation in operations.values():
            request_body = operation.get("request_body") or {}
            for media in (request_body.get("content") or {}).values():
                schema = media.get("schema") or {}
                ref = schema.get("$ref")
                if isinstance(ref, str) and ref.startswith("#/components/schemas/"):
                    referenced_schema_names.add(ref.rsplit("/", 1)[-1])

    referenced_schemas = {
        name: schemas.get(name)
        for name in sorted(referenced_schema_names)
        if name in schemas
    }

    reference_values = {
        "countries": {
            "status_code": country_response.status_code,
            "payload": _safe_json(country_response),
        },
        "pollutants": {
            "status_code": pollutant_response.status_code,
            "payload": _safe_json(pollutant_response),
        },
        "cities": {
            "status_code": city_response.status_code,
            "payload": _safe_json(city_response),
        },
        "verified_pm25_2024_summary": {
            "status_code": summary_response.status_code,
            "request": summary_payload,
            "payload": _safe_json(summary_response),
        },
    }

    return {
        "status": "available" if paths else "empty",
        "swagger_url": SWAGGER_URL,
        "api_title": payload.get("info", {}).get("title"),
        "api_version": payload.get("info", {}).get("version"),
        "path_count": len(paths),
        "interesting_paths": interesting,
        "referenced_request_schemas": referenced_schemas,
        "reference_values": reference_values,
        "ready_for_endpoint_design": bool(
            interesting
            and country_response.is_success
            and pollutant_response.is_success
            and city_response.is_success
            and summary_response.is_success
        ),
    }
