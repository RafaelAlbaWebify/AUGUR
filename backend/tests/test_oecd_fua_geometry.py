from __future__ import annotations

import io
import zipfile

import pytest
import shapefile

from app.ingestion import oecd_fua_geometry as module


WGS84_PRJ = (
    'GEOGCS["WGS 84",DATUM["WGS_1984",'
    'SPHEROID["WGS 84",6378137,298.257223563]],'
    'PRIMEM["Greenwich",0],UNIT["degree",0.0174532925199433]]'
)


def _archive(records, *, projection=WGS84_PRJ):
    shp = io.BytesIO()
    shx = io.BytesIO()
    dbf = io.BytesIO()

    writer = shapefile.Writer(shp=shp, shx=shx, dbf=dbf)
    writer.field("AREA_ID", "C")
    writer.field("NAME", "C")
    for code, name, coords in records:
        writer.poly([coords])
        writer.record(code, name)
    writer.close()

    payload = io.BytesIO()
    with zipfile.ZipFile(payload, "w") as archive:
        archive.writestr("boundaries.shp", shp.getvalue())
        archive.writestr("boundaries.shx", shx.getvalue())
        archive.writestr("boundaries.dbf", dbf.getvalue())
        archive.writestr("boundaries.prj", projection)
    return payload.getvalue()


REGISTERED = [
    {
        "geo_id": "OECD_FUA:AUS01C",
        "country_iso3": "AUS",
        "geography_system": "OECD_FUA",
        "geo_level": "city",
        "source_geo_code": "AUS01C",
    },
    {
        "geo_id": "OECD_FUA:AUS01F",
        "country_iso3": "AUS",
        "geography_system": "OECD_FUA",
        "geo_level": "fua",
        "source_geo_code": "AUS01F",
    },
]


def test_geometry_archive_matches_registered_code_without_fixed_field_name():
    payload = _archive([
        (
            "AUS01F",
            "Sydney FUA",
            [
                [150.7, -34.2],
                [151.5, -34.2],
                [151.5, -33.5],
                [150.7, -33.5],
                [150.7, -34.2],
            ],
        ),
        (
            "CAN01F",
            "Toronto FUA",
            [
                [-80.0, 43.0],
                [-79.0, 43.0],
                [-79.0, 44.0],
                [-80.0, 43.0],
            ],
        ),
    ])

    rows = module.geometry_rows_from_archive(
        payload,
        registered_geographies=REGISTERED,
        expected_level="fua",
    )

    assert len(rows) == 1
    row = rows[0]
    assert row["geo_id"] == "OECD_FUA:AUS01F"
    assert row["source_geo_code"] == "AUS01F"
    assert row["country_iso3"] == "AUS"
    assert row["bbox_min_lon"] == 150.7
    assert row["bbox_max_lon"] == 151.5
    assert '"type":"Polygon"' in row["geometry_geojson"]


def test_geometry_archive_rejects_unverified_projection():
    payload = _archive(
        [
            (
                "AUS01F",
                "Sydney FUA",
                [
                    [0, 0],
                    [1, 0],
                    [1, 1],
                    [0, 0],
                ],
            )
        ],
        projection='PROJCS["Unknown projected CRS"]',
    )

    with pytest.raises(ValueError, match="not verified as WGS84"):
        module.geometry_rows_from_archive(
            payload,
            registered_geographies=REGISTERED,
            expected_level="fua",
        )


def test_geometry_sync_persists_city_and_fua(monkeypatch):
    city_payload = _archive([
        (
            "AUS01C",
            "Greater Sydney",
            [
                [151.0, -34.0],
                [151.4, -34.0],
                [151.4, -33.6],
                [151.0, -34.0],
            ],
        )
    ])
    fua_payload = _archive([
        (
            "AUS01F",
            "Sydney FUA",
            [
                [150.7, -34.2],
                [151.5, -34.2],
                [151.5, -33.5],
                [150.7, -34.2],
            ],
        )
    ])

    monkeypatch.setattr(
        module,
        "geographies_for_country",
        lambda country_iso3: REGISTERED,
    )
    stored = []
    monkeypatch.setattr(
        module,
        "upsert_geography_geometries",
        lambda rows: stored.extend(rows) or len(rows),
    )

    result = module.sync_oecd_fua_geometries(
        "AUS",
        city_payload=city_payload,
        fua_payload=fua_payload,
    )

    assert result["status"] == "available"
    assert result["rows"] == 2
    assert result["city_rows"] == 1
    assert result["fua_rows"] == 1
    assert result["complete"] is True
    assert {row["geo_id"] for row in stored} == {
        "OECD_FUA:AUS01C",
        "OECD_FUA:AUS01F",
    }


def test_geometry_fetch_classifies_oecd_access_restriction():
    import httpx

    request = httpx.Request("GET", module.CITY_BOUNDARIES_URL)

    class Client:
        def get(self, url):
            return httpx.Response(
                403,
                request=request,
            )

    with pytest.raises(module.GeometrySourceRestricted):
        module.fetch_archive(
            module.CITY_BOUNDARIES_URL,
            client=Client(),
        )
