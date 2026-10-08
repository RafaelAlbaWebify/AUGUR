from __future__ import annotations

import io
import json
import zipfile

import httpx


CITY_BOUNDARIES_URL = (
    "https://www.oecd.org/content/dam/oecd/en/data/datasets/"
    "oecd-definition-of-cities-and-functional-urban-areas/"
    "cities%20%284%29.zip"
)
FUA_BOUNDARIES_URL = (
    "https://www.oecd.org/content/dam/oecd/en/data/datasets/"
    "oecd-definition-of-cities-and-functional-urban-areas/"
    "fuas%20%281%29.zip"
)


def inspect_archive(client: httpx.Client, label: str, url: str) -> dict:
    response = client.get(url)
    response.raise_for_status()

    archive = zipfile.ZipFile(io.BytesIO(response.content))
    members = sorted(
        name
        for name in archive.namelist()
        if not name.endswith("/")
    )
    stems = sorted({
        name.rsplit(".", 1)[0]
        for name in members
        if "." in name
    })
    extensions = sorted({
        "." + name.rsplit(".", 1)[1].lower()
        for name in members
        if "." in name
    })

    shapefiles = [
        name for name in members
        if name.lower().endswith(".shp")
    ]
    dbfs = [
        name for name in members
        if name.lower().endswith(".dbf")
    ]
    projections = [
        name for name in members
        if name.lower().endswith(".prj")
    ]

    return {
        "label": label,
        "url": str(response.request.url),
        "http_status": response.status_code,
        "content_type": response.headers.get("content-type"),
        "download_bytes": len(response.content),
        "member_count": len(members),
        "members": members[:80],
        "extensions": extensions,
        "dataset_stems": stems[:40],
        "shapefile_count": len(shapefiles),
        "dbf_count": len(dbfs),
        "projection_count": len(projections),
        "shapefiles": shapefiles[:20],
        "ready_for_geometry_parser": bool(
            shapefiles and dbfs and projections
        ),
    }


def main() -> int:
    with httpx.Client(
        timeout=httpx.Timeout(180.0),
        follow_redirects=True,
        headers={"User-Agent": "AUGUR/0.1"},
    ) as client:
        city = inspect_archive(
            client,
            "cities",
            CITY_BOUNDARIES_URL,
        )
        fua = inspect_archive(
            client,
            "fuas",
            FUA_BOUNDARIES_URL,
        )

    payload = {
        "source_id": "OECD",
        "geography_system": "OECD_FUA",
        "archives": [city, fua],
        "ready_for_geometry_parser": (
            city["ready_for_geometry_parser"]
            and fua["ready_for_geometry_parser"]
        ),
    }
    print(json.dumps(payload, indent=2))
    return 0 if payload["ready_for_geometry_parser"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
