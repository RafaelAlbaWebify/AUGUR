from app.ingestion import cedefop_reset as module


def test_reset_resolver_extracts_official_xlsx_link():
    class Response:
        status_code = 200
        url = module.DATASET_PAGE_URL
        text = (
            '<a href="/files/reset_dataset_2026.xlsx">'
            'Regional skills ecosystem index - dataset</a>'
        )

        def raise_for_status(self):
            return None

    class Client:
        def get(self, url, follow_redirects=True):
            assert url == module.DATASET_PAGE_URL
            return Response()

    result = module.resolve_download_url(Client())

    assert result["status"] == "available"
    assert result["download_url"] == (
        "https://www.cedefop.europa.eu/files/reset_dataset_2026.xlsx"
    )


def test_reset_resolver_keeps_403_explicit():
    class Response:
        status_code = 403

    class Client:
        def get(self, url, follow_redirects=True):
            return Response()

    result = module.resolve_download_url(Client())

    assert result == {
        "status": "access_blocked",
        "status_code": 403,
        "dataset_page_url": module.DATASET_PAGE_URL,
        "download_url": None,
    }
