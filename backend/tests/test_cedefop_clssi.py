from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.ingestion import cedefop_clssi as module


def test_detect_sheet_schema_finds_country_occupation_and_clssi_index():
    rows = [
        ["Cedefop Labour and Skills Shortage Index"],
        [],
        [
            "Country",
            "Country code",
            "Occupation",
            "ISCO-08",
            "CLSSI index",
            "2035",
        ],
        [
            "Ireland",
            "IE",
            "ICT professionals",
            "25",
            3,
            3,
        ],
    ]

    result = module.detect_sheet_schema(rows)

    assert result["status"] == "candidate"
    assert result["header_row_index"] == 2
    assert result["matches"]["country"] == 0
    assert result["matches"]["country_code"] == 1
    assert result["matches"]["occupation"] == 2
    assert result["matches"]["isco"] == 3
    assert result["matches"]["index"] == 4
    assert result["year_columns"] == {2035: 5}


def test_detect_sheet_schema_does_not_guess_unrelated_table():
    rows = [
        ["Notes", "Value"],
        ["Source", "Cedefop"],
        ["Version", "2026"],
    ]

    result = module.detect_sheet_schema(rows)

    assert result["status"] == "unrecognised"
    assert result["has_country"] is False
    assert result["has_occupation"] is False


class FakeResponse:
    def __init__(
        self,
        *,
        content: bytes,
        content_type: str,
        url: str,
    ):
        self.content = content
        self.headers = {"content-type": content_type}
        self.url = url

    def raise_for_status(self):
        return None


class FakeClient:
    def __init__(self, response):
        self.response = response

    def get(self, url):
        return self.response


def test_download_workbook_accepts_official_xlsx_payload(tmp_path):
    path = tmp_path / "clssi.xlsx"
    client = FakeClient(
        FakeResponse(
            content=b"PK\x03\x04fake-xlsx",
            content_type=(
                "application/vnd.openxmlformats-officedocument."
                "spreadsheetml.sheet"
            ),
            url=module.DOWNLOAD_URL,
        )
    )

    result = module.download_workbook(
        path,
        client=client,
    )

    assert result["path"] == str(path)
    assert result["bytes"] == len(b"PK\x03\x04fake-xlsx")
    assert path.read_bytes().startswith(b"PK")


def test_download_workbook_rejects_non_xlsx_payload(tmp_path):
    path = tmp_path / "clssi.xlsx"
    client = FakeClient(
        FakeResponse(
            content=b"<html>blocked</html>",
            content_type="text/html",
            url="https://example.test/error",
        )
    )

    with pytest.raises(RuntimeError, match="did not return an XLSX"):
        module.download_workbook(
            path,
            client=client,
        )

    assert not path.exists()
