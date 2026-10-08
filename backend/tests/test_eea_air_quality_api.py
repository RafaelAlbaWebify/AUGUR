import httpx

from app.ingestion import eea_air_quality_api as module


def test_eea_post_retry_recovers_from_transient_read_error(monkeypatch):
    class Client:
        def __init__(self):
            self.calls = 0

        def post(self, url, json):
            self.calls += 1
            if self.calls == 1:
                raise httpx.ReadError("connection reset")
            return object()

    client = Client()
    monkeypatch.setattr(module.time, "sleep", lambda seconds: None)

    response = module._post_with_retry(
        client,
        "https://example.test",
        json={"example": True},
        attempts=3,
    )

    assert response is not None
    assert client.calls == 2
