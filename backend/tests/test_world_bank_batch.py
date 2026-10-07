from app.ingestion import world_bank as module
from app.ingestion.world_bank import WorldBankAdapter


class Response:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


class Client:
    def __init__(self, payload):
        self.payload = payload
        self.calls = []

    def get(self, url, params=None):
        self.calls.append((url, params))
        return Response(self.payload)


def test_world_bank_batch_query_uses_multiple_country_path(monkeypatch):
    payload = [
        {
            "pages": 1,
            "lastupdated": "2026-10-01",
        },
        [
            {
                "countryiso3code": "ESP",
                "date": "2025",
                "value": 10.0,
                "obs_status": "",
                "decimal": 1,
            },
            {
                "countryiso3code": "DEU",
                "date": "2025",
                "value": 20.0,
                "obs_status": "",
                "decimal": 1,
            },
        ],
    ]
    client = Client(payload)
    stored = []
    monkeypatch.setattr(
        module,
        "upsert_observations",
        lambda rows: stored.extend(rows) or len(rows),
    )
    monkeypatch.setattr(
        module,
        "world_bank_indicators",
        lambda: [{
            "indicator_id": "population_total",
            "source_indicator": "SP.POP.TOTL",
            "unit": "persons",
        }],
    )

    adapter = WorldBankAdapter(client=client)
    result = adapter.sync_countries(["ESP", "DEU"])

    assert len(client.calls) == 1
    url, params = client.calls[0]
    assert "/country/DEU;ESP/indicator/SP.POP.TOTL" in url
    assert params["per_page"] == 20000
    assert result["rows"] == 2
    assert {row["country_iso3"] for row in stored} == {"DEU", "ESP"}


def test_world_bank_large_batch_uses_all_country_endpoint(monkeypatch):
    countries = [
        f"A{chr(65 + ((index // 26) % 26))}{chr(65 + (index % 26))}"
        for index in range(30)
    ]
    payload = [
        {"pages": 1, "lastupdated": "2026-10-01"},
        [],
    ]
    client = Client(payload)
    monkeypatch.setattr(
        module,
        "world_bank_indicators",
        lambda: [{
            "indicator_id": "population_total",
            "source_indicator": "SP.POP.TOTL",
            "unit": "persons",
        }],
    )
    monkeypatch.setattr(
        module,
        "upsert_observations",
        lambda rows: len(rows),
    )

    adapter = WorldBankAdapter(client=client)
    adapter.sync_countries(countries)

    assert len(client.calls) == 1
    assert "/country/all/indicator/SP.POP.TOTL" in client.calls[0][0]
