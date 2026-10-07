from io import BytesIO
import zipfile

from app.ingestion import eea_health_burden as module


class FakeResponse:
    content = b""

    def raise_for_status(self):
        return None


class FakeClient:
    def __init__(self, payload):
        self.payload = payload

    def get(self, url):
        response = FakeResponse()
        response.content = self.payload
        return response


def _archive_bytes():
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr(
            "data.csv",
            "geo;year;value\nES12;2023;12.5\nIE06;2023;4.2\n",
        )
        archive.writestr("README.txt", "documentation only")
    return buffer.getvalue()


def test_health_burden_inspector_discovers_tabular_schema():
    result = module.inspect_eea_pm25_burden_dataset(
        client=FakeClient(_archive_bytes()),
    )

    assert result["status"] == "available"
    assert result["ready_for_parser_design"] is True
    assert result["member_count"] == 2
    assert result["tabular_member_count"] == 2
    sample = next(
        item for item in result["tabular_samples"]
        if item["member"] == "data.csv"
    )
    assert sample["delimiter"] == ";"
    assert sample["headers"] == ["geo", "year", "value"]
    assert sample["sample_rows"][0] == ["ES12", "2023", "12.5"]


def test_health_burden_inspector_is_read_only_metadata():
    result = module.inspect_eea_pm25_burden_dataset(
        client=FakeClient(_archive_bytes()),
    )

    assert result["dataset_id"] == "EEA_PM25_PREMATURE_DEATHS_NUTS23"
    assert result["dataset_version"].endswith("2005-2023_v01_r00")
    assert any(
        "read-only" in note.lower()
        for note in result["notes"]
    )


def _realistic_archive_bytes():
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr(
            f"{module.DATASET_VERSION}/{module.DATASET_VERSION}.csv",
            (
                "code,dimension,dimension_label,unit,unit_label,geo,geo_label,time,obs_value,obs_status\n"
                "11_52,PMD,Premature deaths - Premature deaths,NR,Number,ES12,Principado de Asturias,2023,812,\n"
                "11_52,YLL,Premature deaths - Years of life lost,NR,Number,ES120,Asturias,2023,9634,e\n"
                "11_52,PMD,Premature deaths - Premature deaths,NR,Number,ES,Spain,2023,20000,\n"
                "11_52,OTHER,Other metric,NR,Number,ES12,Principado de Asturias,2023,1,\n"
                "11_52,PMD,Premature deaths - Premature deaths,NR,Number,PT11,Norte,2023,400,\n"
            ),
        )
    return buffer.getvalue()


def test_health_burden_parser_preserves_nuts_granularity_and_metadata():
    rows = module.parse_eea_pm25_burden_archive(
        _realistic_archive_bytes(),
        country_prefixes={"ES"},
    )

    assert len(rows) == 2
    nuts2 = next(row for row in rows if row["geo_code"] == "ES12")
    nuts3 = next(row for row in rows if row["geo_code"] == "ES120")

    assert nuts2["geo_level"] == "NUTS2"
    assert nuts2["burden_type"] == "PMD"
    assert nuts2["unit_code"] == "NR"
    assert nuts2["value"] == 812.0
    assert nuts2["dataset_version"] == module.DATASET_VERSION

    assert nuts3["geo_level"] == "NUTS3"
    assert nuts3["burden_type"] == "YLL"
    assert nuts3["obs_status"] == "e"


def test_health_burden_parser_excludes_national_and_other_country_rows():
    rows = module.parse_eea_pm25_burden_archive(
        _realistic_archive_bytes(),
        country_prefixes={"ES"},
    )

    assert {row["geo_code"] for row in rows} == {"ES12", "ES120"}
    assert {row["burden_type"] for row in rows} == {"PMD", "YLL"}
