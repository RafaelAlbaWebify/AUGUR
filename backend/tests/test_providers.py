from app.providers import PROVIDERS, providers_for_country


def test_provider_ids_are_unique():
    ids = [provider.provider_id for provider in PROVIDERS]
    assert len(ids) == len(set(ids))


def test_spain_uses_all_core_providers():
    ids = {provider.provider_id for provider in providers_for_country("ESP")}
    assert ids == {"WORLD_BANK", "EUROSTAT", "OECD", "IMF", "UN_WPP"}


def test_portugal_uses_all_core_providers():
    ids = {provider.provider_id for provider in providers_for_country("PRT")}
    assert ids == {"WORLD_BANK", "EUROSTAT", "OECD", "IMF", "UN_WPP"}


def test_ireland_uses_all_core_providers():
    ids = {provider.provider_id for provider in providers_for_country("IRL")}
    assert ids == {"WORLD_BANK", "EUROSTAT", "OECD", "IMF", "UN_WPP"}


def test_dynamic_country_provider_selection_uses_registered_metadata(monkeypatch):
    from app import providers as module

    monkeypatch.setattr(
        module,
        "country_record",
        lambda iso3: {
            "iso3": "DEU",
            "eu_member": True,
            "oecd_member": True,
        } if iso3.upper() == "DEU" else None,
    )

    ids = {
        provider.provider_id
        for provider in module.providers_for_country("DEU")
    }

    assert ids == {"WORLD_BANK", "EUROSTAT", "OECD", "IMF", "UN_WPP"}
