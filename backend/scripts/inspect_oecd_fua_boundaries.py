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
    archives = []
    restricted = []

    with httpx.Client(
        timeout=httpx.Timeout(180.0),
        follow_redirects=True,
        headers={"User-Agent": "AUGUR/0.1"},
    ) as client:
        for label, url in (
            ("cities", CITY_BOUNDARIES_URL),
            ("fuas", FUA_BOUNDARIES_URL),
        ):
            try:
                archives.append(
                    inspect_archive(client, label, url)
                )
            except httpx.HTTPStatusError as exc:
                status_code = exc.response.status_code
                if status_code in {401, 403}:
                    restricted.append({
                        "label": label,
                        "url": str(exc.request.url),
                        "http_status": status_code,
                        "status": "source_access_restricted_in_ci",
                    })
                    continue
                raise

    ready = (
        len(archives) == 2
        and all(
            archive["ready_for_geometry_parser"]
            for archive in archives
        )
    )
    payload = {
        "source_id": "OECD",
        "geography_system": "OECD_FUA",
        "archives": archives,
        "restricted_archives": restricted,
        "ready_for_geometry_parser": ready,
        "status": (
            "available"
            if ready
            else "source_access_restricted_in_ci"
            if restricted
            else "unavailable"
        ),
        "notes": [
            (
                "OECD publishes official city and FUA boundary archives, "
                "but automated access to www.oecd.org/content/dam may be "
                "restricted from hosted runners."
            ),
            (
                "AUGUR does not substitute estimated or third-party geometry "
                "for the OECD source-native CITY/FUA identifiers."
            ),
        ],
    }
    print(json.dumps(payload, indent=2))
    return 0 if ready or restricted else 2


if __name__ == "__main__":
    raise SystemExit(main())
