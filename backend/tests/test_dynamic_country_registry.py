from app.catalog import country_membership_flags
from app.ingestion import world_bank as world_bank_module
from app.ingestion.world_bank import WorldBankAdapter
from app.providers import providers_for_country
from app.services import country as country_module


class FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


class FakeClient:
    def __init__(self, responses):
        self.responses = responses
        self.calls = []

    def get(self, url, params=None):
        self.calls.append((url, params))
        return FakeResponse(self.responses[url])


def test_membership_flags_cover_non_pilot_countries():
    assert country_membership_flags("DEU") == {
        "eu_member": True,
        "eurozone_member": True,
        "oecd_member": True,
    }
    assert country_membership_flags("USA") == {
        "eu_member": False,
        "eurozone_member": False,
        "oecd_member": True,
    }
    assert country_membership_flags("IND") == {
        "eu_member": False,
        "eurozone_member": False,
        "oecd_member": False,
    }


def test_world_bank_metadata_registers_non_pilot_country(monkeypatch):
    url = "https://api.worldbank.org/v2/country/DEU"
    client = FakeClient({
        url: [
            {"page": 1},
            [{
                "id": "DEU",
                "iso2Code": "DE",
                "name": "Germany",
                "region": {"value": "Europe & Central Asia"},
                "adminregion": {"value": ""},
            }],
        ]
    })
    stored = []
    monkeypatch.setattr(
        world_bank_module,
        "upsert_country",
        lambda country: stored.append(dict(country)),
    )

    adapter = WorldBankAdapter(client=client)
    metadata = adapter.ensure_country_registered("deu")

    assert metadata["iso3"] == "DEU"
    assert metadata["iso2"] == "DE"
    assert metadata["name"] == "Germany"
    assert metadata["eu_member"] is True
    assert metadata["eurozone_member"] is True
    assert metadata["oecd_member"] is True
    assert stored == [metadata]


def test_world_bank_catalog_filters_aggregates(monkeypatch):
    url = "https://api.worldbank.org/v2/country"
    client = FakeClient({
        url: [
            {"pages": 1},
            [
                {
                    "id": "DEU",
                    "iso2Code": "DE",
                    "name": "Germany",
                    "region": {"value": "Europe & Central Asia"},
                    "adminregion": {"value": ""},
                },
                {
                    "id": "WLD",
                    "iso2Code": "1W",
                    "name": "World",
                    "region": {"value": "Aggregates"},
                    "adminregion": {"value": ""},
                },
            ],
        ]
    })
    stored = []
    monkeypatch.setattr(
        world_bank_module,
        "upsert_country",
        lambda country: stored.append(dict(country)),
    )

    adapter = WorldBankAdapter(client=client)
    countries = adapter.register_country_catalog()

    assert [country["iso3"] for country in countries] == ["DEU"]
    assert [country["iso3"] for country in stored] == ["DEU"]


def test_provider_selection_uses_dynamic_membership_metadata():
    germany = {
        "iso3": "DEU",
        "eu_member": True,
        "oecd_member": True,
    }
    usa = {
        "iso3": "USA",
        "eu_member": False,
        "oecd_member": True,
    }
    india = {
        "iso3": "IND",
        "eu_member": False,
        "oecd_member": False,
    }

    assert {
        provider.provider_id
        for provider in providers_for_country("DEU", country=germany)
    } == {"WORLD_BANK", "EUROSTAT", "OECD", "IMF", "UN_WPP"}

    assert {
        provider.provider_id
        for provider in providers_for_country("USA", country=usa)
    } == {"WORLD_BANK", "OECD", "IMF", "UN_WPP"}

    assert {
        provider.provider_id
        for provider in providers_for_country("IND", country=india)
    } == {"WORLD_BANK", "IMF", "UN_WPP"}


def test_country_selector_catalog_hides_unsynced_discovered_countries(monkeypatch):
    monkeypatch.setattr(
        country_module,
        "country_analysis_coverage",
        lambda: [
            {
                "iso3": "ESP",
                "name": "Spain",
                "analysis_status": "registered_no_evidence",
            },
            {
                "iso3": "DEU",
                "name": "Germany",
                "analysis_status": "available",
            },
            {
                "iso3": "JPN",
                "name": "Japan",
                "analysis_status": "registered_no_evidence",
            },
        ],
    )

    visible = country_module.list_countries()

    assert [country["iso3"] for country in visible] == ["ESP", "DEU"]
