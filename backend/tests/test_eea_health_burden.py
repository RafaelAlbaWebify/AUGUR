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
