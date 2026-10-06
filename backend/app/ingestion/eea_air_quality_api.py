from __future__ import annotations

import httpx


SWAGGER_URL = (
    "https://eeadmz1-downloads-api-appservice.azurewebsites.net/"
    "swagger/v1/swagger.json"
)


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
                }
                for method, operation in operations.items()
                if method.lower() in {"get", "post"}
            }

    return {
        "status": "available" if paths else "empty",
        "swagger_url": SWAGGER_URL,
        "api_title": payload.get("info", {}).get("title"),
        "api_version": payload.get("info", {}).get("version"),
        "path_count": len(paths),
        "interesting_paths": interesting,
        "ready_for_endpoint_design": bool(interesting),
    }
